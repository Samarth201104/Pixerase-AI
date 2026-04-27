import os
import uuid
import logging
import threading

import torch
import gdown
from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
from PIL import Image

# Project-specific model loaders
from background.model_loader import load_u2net, predict_mask
from background.background_removal import (
    composite_foreground_with_bg,
    refine_mask,
    load_template_background
)
from object.infer import (
    load_object_model,
    run_migan_inference,
    grabcut_with_rect,
    grabcut_with_brush,
)

# ==================== CONFIG & LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixerase")

# Use CPU only and limit threads to reduce RAM/CPU usage on free tiers
torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
torch.set_grad_enabled(False)
try:
    torch.backends.cudnn.enabled = False
except Exception:
    pass

# Directories
UPLOAD = "uploads"
OUTPUT = "outputs"
TEMPLATE_BG = "backgrounds"
MODELS_DIR = os.environ.get("MODELS_DIR", "models")

os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)
os.makedirs(TEMPLATE_BG, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Model filenames (where models will be stored locally)
BG_MODEL_PATH = os.path.join(MODELS_DIR, "u2net.pth")
OBJECT_MODEL_PATH = os.path.join(MODELS_DIR, "migan_512_places2.pt")

# Google Drive FILE_ID environment variables (user-provided)
BG_MODEL_FILE_ID = os.environ.get("BG_MODEL_FILE_ID")
OBJECT_MODEL_FILE_ID = os.environ.get("OBJECT_MODEL_FILE_ID")

# Control flags
SKIP_MODEL_DOWNLOAD = os.environ.get("SKIP_MODEL_DOWNLOAD", "false").lower() in ("1", "true", "yes")

DEVICE = torch.device("cpu")

# Globals for loaded models
bg_model = None
migan_model = None

# ==================== UTILITIES ====================

def download_from_gdrive(file_id: str, dest_path: str, quiet: bool = True) -> bool:
    """Download a file from Google Drive using gdown and a FILE_ID.
    Returns True if download succeeded or file already exists."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        logger.info("Model already exists at %s, skipping download", dest_path)
        return True

    if not file_id:
        logger.warning("No FILE_ID provided for %s", dest_path)
        return False

    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        logger.info("Downloading model %s from Google Drive (id=%s)", dest_path, file_id)
        # gdown supports direct id-based URLs
        gdown.download(url, dest_path, quiet=quiet)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            logger.info("Downloaded model to %s", dest_path)
            return True
        else:
            logger.error("Download finished but file missing or empty: %s", dest_path)
            return False
    except Exception as e:
        logger.exception("Failed to download model id=%s: %s", file_id, e)
        return False


def safe_load_bg_model(path: str):
    """Load background model with CPU map_location and minimal memory footprint."""
    try:
        logger.info("Loading background model from %s", path)
        model = load_u2net(path, device=str(DEVICE))
        # set model to eval and move to CPU explicitly
        try:
            model.eval()
            model.to(DEVICE)
        except Exception:
            pass
        logger.info("Background model loaded")
        return model
    except Exception as e:
        logger.exception("Error loading background model: %s", e)
        return None


def safe_load_object_model(path: str):
    """Load object model with CPU map_location and minimal memory footprint."""
    try:
        logger.info("Loading object model from %s", path)
        model = load_object_model(path, device=str(DEVICE))
        try:
            model.eval()
            model.to(DEVICE)
        except Exception:
            pass
        logger.info("Object model loaded")
        return model
    except Exception as e:
        logger.exception("Error loading object model: %s", e)
        return None


def prepare_models():
    """Ensure models are downloaded and loaded once at startup."""
    global bg_model, migan_model

    if SKIP_MODEL_DOWNLOAD:
        logger.info("SKIP_MODEL_DOWNLOAD is set; skipping download step")
    else:
        # Download models if missing
        if BG_MODEL_FILE_ID:
            download_from_gdrive(BG_MODEL_FILE_ID, BG_MODEL_PATH, quiet=True)
        else:
            logger.warning("BG_MODEL_FILE_ID not set; background model will not be downloaded")

        if OBJECT_MODEL_FILE_ID:
            download_from_gdrive(OBJECT_MODEL_FILE_ID, OBJECT_MODEL_PATH, quiet=True)
        else:
            logger.warning("OBJECT_MODEL_FILE_ID not set; object model will not be downloaded")

    # Load models into memory (CPU only)
    try:
        if os.path.exists(BG_MODEL_PATH):
            bg_model = safe_load_bg_model(BG_MODEL_PATH)
        else:
            logger.warning("Background model file not found at %s", BG_MODEL_PATH)

        if os.path.exists(OBJECT_MODEL_PATH):
            migan_model = safe_load_object_model(OBJECT_MODEL_PATH)
        else:
            logger.warning("Object model file not found at %s", OBJECT_MODEL_PATH)
    except Exception:
        logger.exception("Unexpected error while preparing models")


# Start model preparation in a background thread during import so Gunicorn master can spawn workers quickly,
# but ensure models are loaded before first request if needed.
_model_thread = threading.Thread(target=prepare_models, daemon=True)
_model_thread.start()

# ==================== FLASK SETUP ====================
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend")
app.config.update(ENV='production', DEBUG=False)
CORS(app)

# ==================== HELPERS ====================

def get_bg_model():
    """Return background model if loaded; otherwise attempt to load synchronously."""
    global bg_model
    if bg_model is None:
        logger.info("Background model not loaded yet; attempting to prepare synchronously")
        prepare_models()
    return bg_model


def get_migan_model():
    global migan_model
    if migan_model is None:
        logger.info("Object model not loaded yet; attempting to prepare synchronously")
        prepare_models()
    return migan_model

# ==================== ROUTES ====================
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Pixerase.AI Backend is running",
        "models": {
            "background": bool(bg_model),
            "object": bool(migan_model)
        }
    })


@app.route("/api/remove-background", methods=["POST"])
def remove_background():
    """Remove background from image"""
    try:
        model = get_bg_model()
        if model is None:
            return jsonify({"error": "Background model not available"}), 503

        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No image uploaded"}), 400

        bg_template = request.form.get("bg_template")

        uid = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD, f"{uid}_input.png")
        output_path = os.path.join(OUTPUT, f"{uid}_output.png")

        file.save(input_path)
        pil_image = Image.open(input_path).convert("RGB")

        bg_image = None
        if bg_template and bg_template != "none":
            bg_image = load_template_background(bg_template, TEMPLATE_BG)

        # Run prediction with no_grad to reduce memory
        with torch.no_grad():
            mask = predict_mask(model, pil_image)
            refined_mask = refine_mask(mask)
            result = composite_foreground_with_bg(pil_image, refined_mask, bg_image)

        result.save(output_path, "PNG")
        try:
            os.remove(input_path)
        except Exception:
            pass

        return send_file(output_path, mimetype="image/png")

    except Exception as e:
        logger.exception("Error in remove_background: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/remove-object", methods=["POST"])
def remove_object():
    """Remove objects from image using mask"""
    try:
        model = get_migan_model()
        if model is None:
            return jsonify({"error": "Object model not available"}), 503

        image_file = request.files.get("image")
        mask_file = request.files.get("mask")

        if not image_file:
            return jsonify({"error": "No image uploaded"}), 400
        if not mask_file:
            return jsonify({"error": "No mask provided"}), 400

        uid = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD, f"{uid}_input.png")
        mask_path = os.path.join(UPLOAD, f"{uid}_mask.png")
        output_path = os.path.join(OUTPUT, f"{uid}_output.png")

        image_file.save(input_path)
        mask_file.save(mask_path)

        # Use brush-based grabcut with the mask
        final_mask_path = grabcut_with_brush(input_path, mask_path)

        # Run GAN inpainting under no_grad
        with torch.no_grad():
            run_migan_inference(
                model,
                input_path,
                final_mask_path,
                output_path,
                device=str(DEVICE)
            )

        # Clean up temporary files
        for p in (input_path, mask_path):
            try:
                os.remove(p)
            except Exception:
                pass
        if os.path.exists(final_mask_path) and final_mask_path != mask_path:
            try:
                os.remove(final_mask_path)
            except Exception:
                pass

        return send_file(output_path, mimetype="image/png")

    except Exception as e:
        logger.exception("Error in remove_object: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/process", methods=["POST"])
def process_image():
    try:
        mode = request.form.get("mode", "background")
        if mode == "background":
            return remove_background()
        elif mode == "object":
            return remove_object()
        else:
            return jsonify({"error": "Invalid mode. Use 'background' or 'object'"}), 400
    except Exception as e:
        logger.exception("Error in process_image: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/templates", methods=["GET"])
def get_templates():
    try:
        templates = []
        if os.path.exists(TEMPLATE_BG):
            for file in os.listdir(TEMPLATE_BG):
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    templates.append({
                        "name": os.path.splitext(file)[0],
                        "filename": file,
                        "url": f"/static/backgrounds/{file}"
                    })
        return jsonify({"templates": templates})
    except Exception as e:
        logger.exception("Error listing templates: %s", e)
        return jsonify({"error": str(e)}), 500


# Gunicorn friendly: app is module-level. If run directly, use Flask built-in server for quick dev.
if __name__ == "__main__":
    logger.info("Starting development server")
    port = int(os.environ.get("PORT", 10000))
    # Ensure models are prepared before accepting requests locally
    if _model_thread.is_alive():
        logger.info("Waiting for model preparation thread to finish...")
        _model_thread.join(timeout=60)
    app.run(host="0.0.0.0", port=port, debug=False)
