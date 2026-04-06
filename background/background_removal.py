import cv2
import numpy as np
from PIL import Image
import os

def refine_mask(mask_np, threshold=200, open_iter=1, close_iter=2, blur_radius=5):
    """
    mask_np: 2D numpy uint8 (0..255)
    returns refined float mask in [0,1] shape (H,W)
    """
    m = mask_np.copy()
    if m.dtype != np.uint8:
        m = (m * 255).astype(np.uint8)

    # Hard threshold
    _, m = cv2.threshold(m, threshold, 255, cv2.THRESH_BINARY)

    # Cleanup mask
    kernel = np.ones((3, 3), np.uint8)
    if open_iter > 0:
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=open_iter)
    if close_iter > 0:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=close_iter)

    # Feather edges
    if blur_radius > 0:
        k = blur_radius * 2 + 1
        m = cv2.GaussianBlur(m, (k, k), 0)

    m = m.astype(np.float32) / 255.0
    return m


def load_template_background(template_name, template_folder):
    """
    Loads background image from template folder
    """
    if not template_name:
        return None

    path = os.path.join(template_folder, template_name)
    if not os.path.exists(path):
        return None

    return Image.open(path).convert("RGB")


def composite_foreground_with_bg(pil_image, mask_float, bg_image=None):
    """
    pil_image: PIL RGB
    mask_float: float32 ndarray [0,1] shape (H,W)
    bg_image: PIL RGB or None
    """

    img = pil_image.convert("RGB")
    W, H = img.size

    # Resize mask if needed
    if mask_float.shape != (H, W):
        mask = cv2.resize(
            (mask_float * 255).astype(np.uint8),
            (W, H),
            interpolation=cv2.INTER_LINEAR
        )
        mask_float = mask.astype(np.float32) / 255.0

    img_np = np.array(img).astype(np.float32)
    mask_3 = np.repeat(mask_float[:, :, None], 3, axis=2)

    if bg_image is not None:
        bg = bg_image.convert("RGB").resize((W, H))
        bg_np = np.array(bg).astype(np.float32)

        out_np = img_np * mask_3 + bg_np * (1.0 - mask_3)
        out_np = np.clip(out_np, 0, 255).astype(np.uint8)
        return Image.fromarray(out_np)

    else:
        # Transparent PNG
        alpha = (mask_float * 255).astype(np.uint8)
        rgba = np.dstack([img_np.astype(np.uint8), alpha])
        return Image.fromarray(rgba, mode="RGBA")
