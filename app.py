import os
import uuid
import logging

import torch
import gdown
from PIL import Image
import gradio as gr

# Model loaders
from background.model_loader import load_u2net, predict_mask
from background.background_removal import (
    composite_foreground_with_bg,
    refine_mask,
    load_template_background
)
from object.infer import (
    load_object_model,
    run_migan_inference,
    grabcut_with_brush,
)

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixerase")

torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
torch.set_grad_enabled(False)

DEVICE = torch.device("cpu")

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

BG_MODEL_PATH = os.path.join(MODELS_DIR, "u2net.pth")
OBJECT_MODEL_PATH = os.path.join(MODELS_DIR, "migan.pt")

BG_MODEL_FILE_ID = os.environ.get("BG_MODEL_FILE_ID")
OBJECT_MODEL_FILE_ID = os.environ.get("OBJECT_MODEL_FILE_ID")

bg_model = None
migan_model = None

# ================= DOWNLOAD =================

def download_model(file_id, path):
    if os.path.exists(path):
        return
    if not file_id:
        raise ValueError(f"Missing FILE_ID for {path}")
    url = f"https://drive.google.com/uc?id={file_id}"
    logger.info(f"Downloading {path}")
    gdown.download(url, path, quiet=False)

# ================= LOAD =================

def load_models():
    global bg_model, migan_model

    if bg_model is None:
        download_model(BG_MODEL_FILE_ID, BG_MODEL_PATH)
        bg_model = load_u2net(BG_MODEL_PATH, device="cpu")
        bg_model.eval()

    if migan_model is None:
        download_model(OBJECT_MODEL_FILE_ID, OBJECT_MODEL_PATH)
        migan_model = load_object_model(OBJECT_MODEL_PATH, device="cpu")
        migan_model.eval()

# ================= FUNCTIONS =================

def remove_background(image, bg_template):
    load_models()

    if image is None:
        raise gr.Error("Upload image")

    image = image.convert("RGB")

    bg_img = None
    if bg_template and bg_template != "None":
        bg_img = load_template_background(bg_template, "backgrounds")

    with torch.no_grad():
        mask = predict_mask(bg_model, image)
        mask = refine_mask(mask)
        result = composite_foreground_with_bg(image, mask, bg_img)

    return result


def remove_object(image, mask):
    load_models()

    if image is None or mask is None:
        raise gr.Error("Upload image + mask")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "input.png")
        msk = os.path.join(tmp, "mask.png")
        out = os.path.join(tmp, "out.png")

        image.save(inp)
        mask.save(msk)

        final_mask = grabcut_with_brush(inp, msk)

        with torch.no_grad():
            run_migan_inference(
                migan_model,
                inp,
                final_mask,
                out,
                device="cpu"
            )

        return Image.open(out)

# ================= UI =================

def create_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# Pixerase AI")

        with gr.Tabs():
            with gr.Tab("Background Removal"):
                img = gr.Image(type="pil")
                template = gr.Textbox(label="Template (optional)")
                out = gr.Image()

                btn = gr.Button("Process")
                btn.click(remove_background, [img, template], out)

            with gr.Tab("Object Removal"):
                img = gr.Image(type="pil")
                mask = gr.Image(type="pil")
                out = gr.Image()

                btn = gr.Button("Process")
                btn.click(remove_object, [img, mask], out)

    return demo

# ================= RUN =================

demo = create_ui()
demo.launch()