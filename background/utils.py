# utils.py
import os
import io
from PIL import Image

def ensure_dirs():
    os.makedirs('static/backgrounds', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/results', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('model', exist_ok=True)

def pil_to_bytes(pil_img, fmt='PNG'):
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    buf.seek(0)
    return buf
