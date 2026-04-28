import os
import io
import logging
import requests
from flask import Flask, request, send_file, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixerase-backend")

# Environment configuration
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
HF_BG_MODEL = os.environ.get("HF_BG_MODEL")
HF_OBJ_MODEL = os.environ.get("HF_OBJ_MODEL")

if not HF_API_TOKEN:
    logger.warning("HF_API_TOKEN not set — Hugging Face requests will fail without it")

app = Flask(__name__)


def call_hf_inference(model_id: str, file_bytes: bytes, params: dict = None):
    """Call the Hugging Face Inference API for a model.

    Sends the image bytes as application/octet-stream. Returns (content, content_type).
    """
    if not model_id:
        raise ValueError("Model id is not configured")

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

    try:
        resp = requests.post(url, headers=headers, data=file_bytes, timeout=60)
    except requests.RequestException as e:
        logger.exception("Error calling Hugging Face inference API")
        raise

    if resp.status_code != 200:
        logger.error("HF inference failed: %s %s", resp.status_code, resp.text[:200])
        raise RuntimeError(f"HF inference failed: {resp.status_code}")

    return resp.content, resp.headers.get("content-type", "application/octet-stream")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/remove_background", methods=["POST"])
def remove_background_api():
    if "image" not in request.files:
        return jsonify({"error": "image file is required (form field 'image')"}), 400

    f = request.files["image"]
    img_bytes = f.read()

    try:
        content, ctype = call_hf_inference(HF_BG_MODEL, img_bytes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if ctype.startswith("image/"):
        return send_file(io.BytesIO(content), mimetype=ctype)
    # otherwise return raw content
    return (content, 200, {"Content-Type": ctype})


@app.route("/api/remove_object", methods=["POST"])
def remove_object_api():
    if "image" not in request.files:
        return jsonify({"error": "image file is required (form field 'image')"}), 400

    f = request.files["image"]
    img_bytes = f.read()

    # if client provided a mask file, forward it in a multipart form if needed by model
    # For now we send only the image bytes — adapt if your HF model expects multipart inputs.
    try:
        content, ctype = call_hf_inference(HF_OBJ_MODEL, img_bytes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if ctype.startswith("image/"):
        return send_file(io.BytesIO(content), mimetype=ctype)
    return (content, 200, {"Content-Type": ctype})


if __name__ == "__main__":
    # Local debug server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))