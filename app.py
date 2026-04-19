import os
import uuid
import torch
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
from flask import render_template

# Background imports
from background.model_loader import load_u2net, predict_mask
from background.background_removal import (
    composite_foreground_with_bg,
    refine_mask,
    load_template_background
)

# Object imports
from object.infer import (
    load_object_model,
    run_migan_inference,
    grabcut_with_rect,
    grabcut_with_brush,
)

# ==================== FLASK SETUP ====================
app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend"
)
CORS(app)  # Enable CORS for all routes

# ==================== PATHS ====================
UPLOAD = "uploads"
OUTPUT = "outputs"
TEMPLATE_BG = "backgrounds"

os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)
os.makedirs(TEMPLATE_BG, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# ==================== LOAD MODELS ====================
# print("Loading models...")
# try:
#     bg_model = load_u2net("background/models/u2net.pth", device=DEVICE)
#     print("✅ Background model loaded")
# except Exception as e:
#     print(f"⚠️ Background model load error: {e}")
#     bg_model = None

# try:
#     migan_model = load_object_model("object/models/migan_512_places2.pt", device=DEVICE)
#     print("✅ Object removal model loaded")
# except Exception as e:
#     print(f"⚠️ Object removal model load error: {e}")
#     migan_model = None


bg_model = None
migan_model = None

def get_bg_model():
    global bg_model
    if bg_model is None:
        print("Loading Background Model...")
        bg_model = load_u2net("background/models/u2net.pth", device=DEVICE)
    return bg_model

def get_migan_model():
    global migan_model
    if migan_model is None:
        print("Loading Object Model...")
        migan_model = load_object_model("object/models/migan_512_places2.pt", device=DEVICE)
    return migan_model


# ==================== HEALTH CHECK ====================
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Pixerase.AI Backend is running",
        "models": {
            "background": True,
            "object": True
        }
    })

# ==================== BACKGROUND REMOVAL API ====================
@app.route("/api/remove-background", methods=["POST"])
def remove_background():
    """Remove background from image"""
    try:
        model = get_bg_model()
        
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No image uploaded"}), 400

        # Get optional background template
        bg_template = request.form.get("bg_template")
        
        # Save uploaded image
        uid = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD, f"{uid}_input.png")
        output_path = os.path.join(OUTPUT, f"{uid}_output.png")
        
        file.save(input_path)
        pil_image = Image.open(input_path).convert("RGB")
        
        # Load template background if specified
        bg_image = None
        if bg_template and bg_template != "none":
            bg_image = load_template_background(bg_template, TEMPLATE_BG)
        
        # Process background removal
        mask = predict_mask(model, pil_image)
        refined_mask = refine_mask(mask)
        result = composite_foreground_with_bg(pil_image, refined_mask, bg_image)
        
        # Save result
        result.save(output_path, "PNG")
        
        # Clean up input file
        os.remove(input_path)
        
        return send_file(output_path, mimetype="image/png")
        
    except Exception as e:
        print(f"Error in remove_background: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== OBJECT REMOVAL API ====================
@app.route("/api/remove-object", methods=["POST"])
def remove_object():
    """Remove objects from image using mask"""
    try:
        model = get_migan_model()
        
        image_file = request.files.get("image")
        mask_file = request.files.get("mask")
        
        if not image_file:
            return jsonify({"error": "No image uploaded"}), 400
        
        if not mask_file:
            return jsonify({"error": "No mask provided"}), 400
        
        # Save files
        uid = uuid.uuid4().hex
        input_path = os.path.join(UPLOAD, f"{uid}_input.png")
        mask_path = os.path.join(UPLOAD, f"{uid}_mask.png")
        output_path = os.path.join(OUTPUT, f"{uid}_output.png")
        
        image_file.save(input_path)
        mask_file.save(mask_path)
        
        # Use brush-based grabcut with the mask
        final_mask_path = grabcut_with_brush(input_path, mask_path)
        
        # Run GAN inpainting
        run_migan_inference(
            model, 
            input_path, 
            final_mask_path, 
            output_path, 
            device=DEVICE
        )
        
        # Clean up temporary files
        os.remove(input_path)
        os.remove(mask_path)
        if os.path.exists(final_mask_path) and final_mask_path != mask_path:
            os.remove(final_mask_path)
        
        return send_file(output_path, mimetype="image/png")
        
    except Exception as e:
        print(f"Error in remove_object: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== UNIFIED API (Handles both modes) ====================
@app.route("/api/process", methods=["POST"])
def process_image():
    """Unified API endpoint for both background and object removal"""
    try:
        mode = request.form.get("mode", "background")
        
        if mode == "background":
            return remove_background()
        elif mode == "object":
            return remove_object()
        else:
            return jsonify({"error": "Invalid mode. Use 'background' or 'object'"}), 400
            
    except Exception as e:
        print(f"Error in process_image: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== TEMPLATE BACKGROUNDS API ====================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/templates", methods=["GET"])
def get_templates():
    """Get list of available background templates"""
    try:
        templates = []
        if os.path.exists(TEMPLATE_BG):
            for file in os.listdir(TEMPLATE_BG):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    templates.append({
                        "name": os.path.splitext(file)[0],
                        "filename": file,
                        "url": f"/static/backgrounds/{file}"
                    })
        return jsonify({"templates": templates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RUN SERVER ====================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Pixerase.AI Backend Server")
    print("="*50)
    print(f"📍 Server running at: http://localhost:5000")
    print(f"🔧 Device: {DEVICE}")
    print(f"✅ Background Model: {'Loaded' if bg_model else 'Not Loaded'}")
    print(f"✅ Object Model: {'Loaded' if migan_model else 'Not Loaded'}")
    print("="*50 + "\n")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)