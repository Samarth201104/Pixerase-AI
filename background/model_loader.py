# model_loader.py
import os
import torch
from PIL import Image
import numpy as np

# import U2NET class from model/u2net.py
try:
    from background.model.u2net import U2NET
except Exception as e:
    raise ImportError("Cannot import U2NET. Ensure model/u2net.py exists and defines U2NET class.") from e

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_u2net(model_path="background/models/u2net.pth", device=DEVICE):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"U2-Net weights not found at '{model_path}'. Place u2net.pth there.")
    net = U2NET(3, 1)
    state = torch.load(model_path, map_location=device)
    # handle DataParallel prefix if present
    if any(k.startswith("module.") for k in state.keys()):
        new_state = {}
        for k, v in state.items():
            new_state[k.replace("module.", "")] = v
        state = new_state
    net.load_state_dict(state)
    net.to(device)
    net.eval()
    return net

def predict_mask(net, pil_image, device=DEVICE, target_size=320):
    """
    Returns mask numpy uint8 (H, W) with values 0..255 resized to input image size.
    """
    import torchvision.transforms as T
    transform = T.Compose([
        T.Resize((target_size, target_size)),
        T.ToTensor(),
        T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])
    img_t = transform(pil_image).unsqueeze(0).to(device)  # 1x3xHxW
    with torch.no_grad():
        outputs = net(img_t)
        # U2NET returns multiple outputs (d1..d7), typically the first is best
        if isinstance(outputs, (list, tuple)):
            pred = outputs[0]
        else:
            pred = outputs
        # pred shape: (B,1,H,W)
        pred_np = pred.squeeze().cpu().numpy()  # shape (H,W) or (1,H,W)
        if pred_np.ndim == 3:
            pred_np = pred_np[0]
        # normalize
        pred_np = (pred_np - pred_np.min()) / (pred_np.max() - pred_np.min() + 1e-8)
        pred_np = (pred_np * 255).astype("uint8")
    # resize to original image size
    mask = Image.fromarray(pred_np).resize(pil_image.size, resample=Image.BILINEAR)
    return np.array(mask)
