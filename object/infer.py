# backend/object/infer.py
import os
import sys
import cv2
import numpy as np
from scipy.ndimage import binary_fill_holes
from PIL import Image, ImageOps, ImageFilter
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.model_zoo.migan_inference import Generator as MIGAN


# -------------------------
# Utility: force multiple of 8
# -------------------------
def make_multiple_of_8(x):
    return (x + 7) // 8 * 8


# -------------------------
# GrabCut (rect)
# -------------------------
def grabcut_with_rect(image_path, rect, iter_count=5):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    mask = np.zeros(image.shape[:2], np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(image, mask, tuple(rect), bgdModel, fgdModel,
                iter_count, cv2.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8") * 255

    filled = binary_fill_holes(mask2 > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    closed = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, kernel, iterations=3)
    dilated = cv2.dilate(closed, kernel, iterations=3)
    final_mask = (dilated * 255).astype(np.uint8)

    mask_path = os.path.splitext(image_path)[0] + "_mask.png"
    cv2.imwrite(mask_path, final_mask)
    return mask_path


# -------------------------
# GrabCut (brush)
# -------------------------
def grabcut_with_brush(image_path, brush_mask_path, iter_count=5):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    h, w = image.shape[:2]

    user_mask = cv2.imread(brush_mask_path, cv2.IMREAD_GRAYSCALE)
    user_mask = cv2.resize(user_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    _, user_mask = cv2.threshold(user_mask, 10, 255, cv2.THRESH_BINARY)

    grabcut_mask = np.zeros((h, w), np.uint8)

    grabcut_mask[user_mask == 255] = cv2.GC_FGD
    grabcut_mask[user_mask == 0] = cv2.GC_BGD

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    cv2.grabCut(image, grabcut_mask, None, bgdModel, fgdModel,
                iter_count, cv2.GC_INIT_WITH_MASK)

    raw_mask = np.where(
        (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD),
        255, 0
    ).astype("uint8")

    filled = binary_fill_holes(raw_mask > 0).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    final_mask = cv2.morphologyEx(filled, cv2.MORPH_CLOSE, kernel, iterations=3)
    final_mask = cv2.dilate(final_mask, kernel, iterations=2)

    mask_path = os.path.splitext(image_path)[0] + "_mask.png"
    cv2.imwrite(mask_path, final_mask)
    return mask_path


# -------------------------
# Load MI-GAN
# -------------------------
def load_object_model(model_path, device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = MIGAN(resolution=512)

    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


# -------------------------
# Run inference (FIXED)
# -------------------------
def run_migan_inference(model, image_path, mask_path_or_array, output_path, device=None):

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    resolution = 512

    img = Image.open(image_path).convert("RGB")

    if isinstance(mask_path_or_array, str):
        mask = Image.open(mask_path_or_array).convert("L")
    else:
        mask = Image.fromarray(mask_path_or_array.astype(np.uint8)).convert("L")

    # Invert mask
    mask = ImageOps.invert(mask)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))

    # Resize while keeping ratio
    w, h = img.size
    if w > h:
        new_w = resolution
        new_h = int(h * (resolution / w))
    else:
        new_h = resolution
        new_w = int(w * (resolution / h))

    # ---- FIX: force multiple of 8 ----
    new_w = make_multiple_of_8(new_w)
    new_h = make_multiple_of_8(new_h)

    img_resized = img.resize((new_w, new_h), Image.BICUBIC)
    mask_resized = mask.resize((new_w, new_h), Image.NEAREST)

    pad_w = (resolution - new_w) // 2 if new_w < resolution else 0
    pad_h = (resolution - new_h) // 2 if new_h < resolution else 0

    img_square = ImageOps.expand(img_resized, (pad_w, pad_h, pad_w, pad_h), fill=0)
    mask_square = ImageOps.expand(mask_resized, (pad_w, pad_h, pad_w, pad_h), fill=255)

    img_arr = np.array(img_square)
    mask_arr = np.array(mask_square)[:, :, np.newaxis] // 255

    img_tensor = torch.Tensor(img_arr).float() * 2 / 255 - 1
    mask_tensor = torch.Tensor(mask_arr).float()

    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)
    mask_tensor = mask_tensor.permute(2, 0, 1).unsqueeze(0)

    x = torch.cat([mask_tensor - 0.5, img_tensor * mask_tensor], dim=1).to(device)

    with torch.no_grad():
        pred = model(x)[0]

    pred = (pred * 0.5 + 0.5).clamp(0, 1) * 255
    pred = pred.to(torch.uint8).permute(1, 2, 0).cpu().numpy()

    result_cropped = pred[pad_h:pad_h + new_h, pad_w:pad_w + new_w]

    mask_np = np.array(mask_resized)[:, :, np.newaxis] // 255
    composed = (
        np.array(img_resized).astype(np.uint8) * mask_np
        + result_cropped.astype(np.uint8) * (1 - mask_np)
    )

    Image.fromarray(composed.astype(np.uint8)).save(output_path)
    return output_path
