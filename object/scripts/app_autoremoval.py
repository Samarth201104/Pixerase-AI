import cv2
import sys
import numpy as np
import argparse
from scipy.ndimage import binary_fill_holes
import os
import torch
from PIL import Image, ImageOps, ImageFilter
from tqdm import tqdm

# 🧠 Fix: Add project root to Python path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MI-GAN model
from lib.model_zoo.migan_inference import Generator as MIGAN



# -----------------------------
# Step 1: Interactive Object Selection
# -----------------------------
def select_object(image_path):
    image = cv2.imread(image_path)
    clone = image.copy()
    rect = []
    drawing = False
    ix, iy = -1, -1

    def draw_rectangle(event, x, y, flags, param):
        nonlocal ix, iy, drawing, rect, clone
        temp = clone.copy()

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            cv2.rectangle(temp, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow("Select Object (Press ENTER when done)", temp)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            rect = [min(ix, x), min(iy, y), abs(x - ix), abs(y - iy)]
            cv2.rectangle(temp, (rect[0], rect[1]), (rect[0]+rect[2], rect[1]+rect[3]), (0, 255, 0), 2)
            cv2.imshow("Select Object (Press ENTER when done)", temp)

    cv2.namedWindow("Select Object (Press ENTER when done)")
    cv2.setMouseCallback("Select Object (Press ENTER when done)", draw_rectangle)

    while True:
        display = clone.copy()
        if rect:
            cv2.rectangle(display, (rect[0], rect[1]), (rect[0]+rect[2], rect[1]+rect[3]), (0, 255, 0), 2)
        cv2.imshow("Select Object (Press ENTER when done)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            break
        elif key == 27:  # ESC
            cv2.destroyAllWindows()
            print("[INFO] Selection cancelled.")
            return None

    cv2.destroyAllWindows()
    return rect


# -----------------------------
# Step 2: GrabCut + Post-processing
# -----------------------------
def generate_mask(image_path, rect):
    image = cv2.imread(image_path)
    mask = np.zeros(image.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(image, mask, tuple(rect), bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8") * 255

    filled_mask = binary_fill_holes(mask2 > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    closed_mask = cv2.morphologyEx(filled_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    dilated_mask = cv2.dilate(closed_mask, kernel, iterations=3)
    final_mask = (dilated_mask * 255).astype(np.uint8)

    mask_path = os.path.splitext(image_path)[0] + "_mask.png"
    cv2.imwrite(mask_path, final_mask)
    print(f"[INFO] Mask generated and saved at: {mask_path}")
    return mask_path


# -----------------------------
# Step 3: Resize with Aspect Ratio
# -----------------------------
def resize_keep_aspect(image, max_size=512, interpolation=Image.BICUBIC):
    """Resize keeping aspect ratio like demo.py."""
    w, h = image.size
    if w > h:
        new_w = max_size
        new_h = int(h * (max_size / w))
    else:
        new_h = max_size
        new_w = int(w * (max_size / h))
    return image.resize((new_w, new_h), interpolation)


# -----------------------------
# Step 4: Run MI-GAN Inference (Inline)
# -----------------------------
def run_migan_inference(image_path, mask_path, model_path, device="cuda"):
    print("[INFO] Loading MI-GAN model...")

    resolution = 512
    model = MIGAN(resolution=resolution)
    model.load_state_dict(torch.load(model_path, map_location=device))
    if device == "cuda":
        model = model.to("cuda")
    model.eval()

    print("[INFO] Running inference...")

    img = Image.open(image_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")

    # Invert mask so black = hole
    mask = ImageOps.invert(mask)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))

    # Step 1: Resize keeping aspect ratio (e.g., 512x320)
    w, h = img.size
    if w > h:
        new_w = resolution
        new_h = int(h * (resolution / w))
    else:
        new_h = resolution
        new_w = int(w * (resolution / h))
    img_resized = img.resize((new_w, new_h), Image.BICUBIC)
    mask_resized = mask.resize((new_w, new_h), Image.NEAREST)

    # Step 2: Center-crop to 512x512 for MI-GAN input
    pad_w = (resolution - new_w) // 2 if new_w < resolution else 0
    pad_h = (resolution - new_h) // 2 if new_h < resolution else 0
    img_square = ImageOps.expand(img_resized, (pad_w, pad_h, pad_w, pad_h), fill=0)
    mask_square = ImageOps.expand(mask_resized, (pad_w, pad_h, pad_w, pad_h), fill=255)

    # Step 3: Convert to tensor input
    img_arr = np.array(img_square)
    mask_arr = np.array(mask_square)[:, :, np.newaxis] // 255
    img_tensor = torch.Tensor(img_arr).float() * 2 / 255 - 1
    mask_tensor = torch.Tensor(mask_arr).float()
    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)
    mask_tensor = mask_tensor.permute(2, 0, 1).unsqueeze(0)
    x = torch.cat([mask_tensor - 0.5, img_tensor * mask_tensor], dim=1)

    if device == "cuda":
        x = x.to("cuda")

    # Step 4: Run MI-GAN inference
    with torch.no_grad():
        result = model(x)[0]
    result = (result * 0.5 + 0.5).clamp(0, 1) * 255
    result = result.to(torch.uint8).permute(1, 2, 0).cpu().numpy()

    # Step 5: Crop back to original rectangular size
    result_cropped = result[pad_h:pad_h+new_h, pad_w:pad_w+new_w]

    # Step 6: Combine with mask
    mask_np = np.array(mask_resized)[:, :, np.newaxis] // 255
    composed = np.array(img_resized) * mask_np + result_cropped * (1 - mask_np)
    composed_img = Image.fromarray(composed.astype(np.uint8))

    output_path = os.path.splitext(image_path)[0] + "_output.png"
    composed_img.save(output_path)
    print(f"[✅] Final image saved at: {output_path}")

    # Step 7: Show final output preview
    cv2.imshow("Final Result - Press any key to close", cv2.cvtColor(np.array(composed_img), cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return output_path



# -----------------------------
# Step 6: Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Automatic Object Removal using MI-GAN + GrabCut")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--model", default="models/migan_512_places2.pt", help="Path to MI-GAN model")
    args = parser.parse_args()

    rect = select_object(args.image)
    if rect is None:
        print("[INFO] No object selected. Exiting.")
        return

    mask_path = generate_mask(args.image, rect)
    run_migan_inference(args.image, mask_path, args.model, device="cuda")


if __name__ == "__main__":
    main()
