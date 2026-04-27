import os
import io
import uuid
import logging
import threading

import torch
import gdown
from PIL import Image
import gradio as gr

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

# ==================== DEPLOYMENT CONFIG ====================
# Deployment target is now primarily Hugging Face Spaces
DEPLOYMENT_TARGET = os.environ.get("DEPLOYMENT_TARGET", "huggingface")  # "huggingface" or "development"

# ==================== CONFIG & LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixerase")

# Deployment-specific optimizations
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
    """Ensure models are downloaded and loaded once at startup based on deployment target."""
    global bg_model, migan_model

    if SKIP_MODEL_DOWNLOAD:
        logger.info("SKIP_MODEL_DOWNLOAD is set; skipping download step")
    else:
        # Download models based on deployment target
        if DEPLOYMENT_TARGET in ["render", "development"]:
            if BG_MODEL_FILE_ID:
                download_from_gdrive(BG_MODEL_FILE_ID, BG_MODEL_PATH, quiet=True)
            else:
                logger.warning("BG_MODEL_FILE_ID not set; background model will not be downloaded")

        if DEPLOYMENT_TARGET in ["huggingface", "development"]:
            if OBJECT_MODEL_FILE_ID:
                download_from_gdrive(OBJECT_MODEL_FILE_ID, OBJECT_MODEL_PATH, quiet=True)
            else:
                logger.warning("OBJECT_MODEL_FILE_ID not set; object model will not be downloaded")

    # Load models into memory based on deployment target
    try:
        if DEPLOYMENT_TARGET in ["render", "development"]:
            if os.path.exists(BG_MODEL_PATH):
                bg_model = safe_load_bg_model(BG_MODEL_PATH)
            else:
                logger.warning("Background model file not found at %s", BG_MODEL_PATH)

        if DEPLOYMENT_TARGET in ["huggingface", "development"]:
            if os.path.exists(OBJECT_MODEL_PATH):
                migan_model = safe_load_object_model(OBJECT_MODEL_PATH)
            else:
                logger.warning("Object model file not found at %s", OBJECT_MODEL_PATH)
    except Exception:
        logger.exception("Unexpected error while preparing models")


# Start model preparation in a background thread
_model_thread = threading.Thread(target=prepare_models, daemon=True)
_model_thread.start()

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
    prepare_models()
    return migan_model


# ==================== GRADIO PROCESSING FUNCTIONS ====================

def remove_background_gradio(image: Image.Image, bg_template: str = None) -> Image.Image:
    """Remove background from image (Gradio version)"""
    try:
        model = get_bg_model()
        if model is None:
            raise gr.Error("Background model not available. Please try again later.")

        if image is None:
            raise gr.Error("Please upload an image")

        # Convert to RGB if needed
        pil_image = image.convert("RGB")

        # Get background template if specified
        bg_image = None
        if bg_template and bg_template != "None":
            bg_image = load_template_background(bg_template, TEMPLATE_BG)

        # Run prediction with no_grad to reduce memory
        with torch.no_grad():
            mask = predict_mask(model, pil_image)
            refined_mask = refine_mask(mask)
            result = composite_foreground_with_bg(pil_image, refined_mask, bg_image)

        return result

    except Exception as e:
        logger.exception("Error in remove_background_gradio: %s", e)
        raise gr.Error(f"Error processing image: {str(e)}")


def remove_object_gradio(image: Image.Image, mask: Image.Image) -> Image.Image:
    """Remove object from image using mask (Gradio version)"""
    try:
        model = get_migan_model()
        if model is None:
            raise gr.Error("Object model not available. Please try again later.")

        if image is None:
            raise gr.Error("Please upload an image")

        if mask is None:
            raise gr.Error("Please provide a mask for the object to remove")

        # Save temporary files
        import tempfile

        uid = uuid.uuid4().hex
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, f"{uid}_input.png")
            mask_path = os.path.join(temp_dir, f"{uid}_mask.png")
            output_path = os.path.join(temp_dir, f"{uid}_output.png")

            # Save images
            image.save(input_path)
            mask.save(mask_path)

            # Process mask with GrabCut
            final_mask_path = grabcut_with_brush(input_path, mask_path)

            # Run GAN inpainting under no_grad
            with torch.no_grad():
                result_path = run_migan_inference(
                    model,
                    input_path,
                    final_mask_path,
                    output_path,
                    device=str(DEVICE)
                )

            # Load result
            result = Image.open(result_path).copy()
            return result

    except Exception as e:
        logger.exception("Error in remove_object_gradio: %s", e)
        raise gr.Error(f"Error processing image: {str(e)}")


# ==================== GRADIO INTERFACE ====================

def create_gradio_interface():
    """Create Gradio interface for Hugging Face Spaces deployment"""

    # Get available background templates
    templates = ["None"]
    if os.path.exists(TEMPLATE_BG):
        for file in os.listdir(TEMPLATE_BG):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                templates.append(os.path.splitext(file)[0])

    with gr.Blocks(title="Pixerase.AI - Background & Object Removal", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
# Pixerase.AI - AI-Powered Image Editing

Remove backgrounds and objects from your images using advanced AI models.
        """)

        with gr.Tabs():
            # Background Removal Tab
            with gr.Tab("Background Removal"):
                with gr.Row():
                    with gr.Column():
                        bg_image_input = gr.Image(label="Input Image", type="pil")
                        bg_template_dropdown = gr.Dropdown(
                            choices=templates,
                            value="None",
                            label="Background Template (Optional)"
                        )
                        bg_submit_btn = gr.Button("Remove Background", variant="primary", size="lg")

                    with gr.Column():
                        bg_output_image = gr.Image(label="Result")

                bg_submit_btn.click(
                    fn=remove_background_gradio,
                    inputs=[bg_image_input, bg_template_dropdown],
                    outputs=bg_output_image
                )

                gr.Markdown("""
## Background Removal Instructions
1. Upload your image
2. (Optional) Select a background template to replace the background
3. Click "Remove Background" to process

The U²-Net model is used for accurate background segmentation.
                """)

            # Object Removal Tab
            with gr.Tab("Object Removal"):
                with gr.Row():
                    with gr.Column():
                        obj_image_input = gr.Image(label="Input Image", type="pil")
                        obj_mask_input = gr.Image(
                            label="Mask Image (white = object to remove)",
                            type="pil",
                            info="Draw white areas on a black background for objects to remove"
                        )
                        obj_submit_btn = gr.Button("Remove Object", variant="primary", size="lg")

                    with gr.Column():
                        obj_output_image = gr.Image(label="Result")

                obj_submit_btn.click(
                    fn=remove_object_gradio,
                    inputs=[obj_image_input, obj_mask_input],
                    outputs=obj_output_image
                )

                gr.Markdown("""
## Object Removal Instructions
1. Upload your image
2. Provide a mask image (white areas = objects to remove, black = areas to keep)
3. Click "Remove Object" to process

The MiGAN model uses GAN-based inpainting for realistic object removal.
                """)

    return demo


# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    # Ensure models are prepared before accepting requests
    if _model_thread.is_alive():
        logger.info("Waiting for model preparation thread to finish...")
        _model_thread.join(timeout=60)

    logger.info("Starting Gradio interface for Hugging Face Spaces deployment")
    demo = create_gradio_interface()
    demo.launch()

