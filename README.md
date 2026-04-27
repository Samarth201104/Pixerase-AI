# Pixerase.AI - Split Deployment Architecture

Pixerase-AI is an advanced AI-powered image editing tool designed for seamless background removal and object inpainting. This project supports deployment on multiple platforms with optimized configurations.

## Architecture Overview

### Deployment Targets

- **Render (Background Removal)**: Flask API for background removal using U2Net
- **Hugging Face Spaces (Object Removal)**: Gradio web interface for object removal using MiGAN
- **Development**: Local development with both services

## Features

- **Background Removal**: Automatically detect and remove backgrounds from images using U2Net model.
- **Object Inpainting**: Fill in removed objects or areas with contextually appropriate content using GAN models like MiGAN.
- **Platform-Specific Optimization**: Memory and performance optimizations for each deployment target.
- **Web Interface**: User-friendly interfaces for easy image upload and processing.

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)
- A virtual environment tool (e.g., venv)

### Local Development

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/pixerase-ai.git
   cd pixerase-ai
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Pre-trained Models**:
   - Download the required model files and place them in the appropriate directories:
     - U²-Net model (`u2net.pth`) → `models/`
     - MI-GAN models (e.g., `migan_512_places2.pt`) → `models/`

5. **Run Development Server**:
   ```bash
   python app.py
   ```

## Deployment

### Render (Background Removal)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following environment variables:
   - `DEPLOYMENT_TARGET`: `render`
   - `BG_MODEL_FILE_ID`: Your Google Drive file ID for U2Net model
   - `TORCH_THREADS`: `1`
   - `SKIP_MODEL_DOWNLOAD`: `false`
4. Use these build settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### Hugging Face Spaces (Object Removal)

1. Create a new Space on Hugging Face
2. Select "Gradio" as the SDK
3. Upload all files from this repository
4. Set environment variables in Space settings:
   - `DEPLOYMENT_TARGET`: `huggingface`
   - `OBJECT_MODEL_FILE_ID`: Your Google Drive file ID for MiGAN model
   - `TORCH_THREADS`: `1`
   - `SKIP_MODEL_DOWNLOAD`: `false`
5. The app will run automatically

## Environment Variables

### Common
- `DEPLOYMENT_TARGET`: `render`, `huggingface`, or `development` (default: development)
- `MODELS_DIR`: Directory to store models (default: "models")
- `TORCH_THREADS`: Number of PyTorch threads (default: 1)
- `SKIP_MODEL_DOWNLOAD`: Skip model download (default: false)

### Background Removal (Render)
- `BG_MODEL_FILE_ID`: Google Drive file ID for U2Net model

### Object Removal (Hugging Face)
- `OBJECT_MODEL_FILE_ID`: Google Drive file ID for MiGAN model

## Testing

Run the deployment test script to verify configurations:

```bash
python test_deployment.py
```

This will test all deployment modes and ensure the app can import correctly for each target platform.

## API Endpoints (Render)

### POST /api/remove-background

Removes the background from an uploaded image.

**Parameters:**
- `image` (file): The image file to process
- `bg_template` (optional): Background template name

**Response:**
- PNG image with transparent background

### GET /api/health

Returns service health status.

## Usage (Hugging Face)

Upload an image and a mask (white areas indicate objects to remove). The service will use GrabCut to refine the mask and MiGAN to inpaint the removed areas.

## Memory Optimization

- **Render**: CPU-only inference, limited threads, optimized for 512MB RAM
- **Hugging Face**: CPU-optimized with opencv-python-headless
- **Development**: Full local development with both services

   ### 🔹 MI-GAN (Object Removal - Inpainting)
   Download from:
   https://github.com/Picsart-AI-Research/MI-GAN

   ### 🔹 U²-Net (Background Removal)
   Download from:
   https://drive.google.com/uc?id=1ao1ovG1Qtx4b7EoskHXmi2E9rp5CHLcZ

## Usage

### Running the Web Application

1. Start the Flask application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000` (or the specified port).

3. Upload an image via the web interface, select the desired operation (background removal or object inpainting), and process it.

### Command-Line Scripts

- **Background Removal**:
  ```bash
  python object/scripts/app_autoremoval.py --input path/to/image.jpg --output path/to/output.jpg
  ```

- **Object Inpainting**:
  ```bash
  python object/main.py --config object/configs/experiment/comodgan_places256.yaml --input path/to/image.jpg --mask path/to/mask.jpg --output path/to/output.jpg
  ```

- **Evaluation**:
  ```bash
  python object/scripts/evaluate_fid_lpips.py --real_dir path/to/real_images --fake_dir path/to/generated_images
  ```

- **Export to ONNX**:
  ```bash
  python object/scripts/create_onnx_pipeline.py --model_path background/models/u2net.pth --output_path outputs/u2net.onnx
  ```

### Configuration

- Modify experiment configurations in `object/configs/experiment/`.
- Adjust model settings in `object/configs/model/`.
- Dataset configurations are in `object/configs/dataset/`.

## Project Structure

```
pixerase-ai/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore file
├── background/                     # Background removal module
│   ├── __init__.py
│   ├── background_removal.py
│   ├── model/                      # U2Net model implementation
│   ├── models/                     # Pre-trained U2Net model weights
│   ├── model_loader.py
│   └── utils.py
├── backgrounds/                    # Template background images
├── frontend/                       # Web interface
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── api-service.js
│   │   ├── app.js
│   │   ├── canvas-manager.js
│   │   ├── image-processor.js
│   │   └── ui-controller.js
│   └── templates/
│       └── index.html
├── object/                         # Object inpainting module
│   ├── infer.py
│   ├── main.py
│   ├── configs/                    # Configuration files
│   │   ├── dataset/
│   │   │   ├── ffhq.yaml
│   │   │   └── places2.yaml
│   │   ├── experiment/
│   │   │   ├── ablation_dw_places256.yaml
│   │   │   ├── ...
│   │   │   └── comodgan_places512.yaml
│   │   └── model/
│   │       ├── comodgan.yaml
│   │       └── migan.yaml
│   ├── dnnlib/
│   │   ├── __init__.py
│   │   └── util.py
│   ├── examples/                   # Example datasets
│   │   ├── messi/
│   │   │   ├── images/
│   │   │   ├── masks/
│   │   │   └── results/
│   │   └── places2_512_object/
│   │       ├── images/
│   │       ├── masks/
│   │       └── results/
│   ├── lib/                        # Core library
│   │   ├── __init__.py
│   │   ├── cfg_helper.py
│   │   ├── cfg_holder.py
│   │   ├── data_factory/
│   │   ├── evaluator/
│   │   ├── experiments/
│   │   ├── log_service.py
│   │   ├── model_zoo/
│   │   └── utils.py
│   ├── models/                     # Pre-trained MI-GAN model weights
│   ├── scripts/                    # Utility scripts
│   │   ├── app_autoremoval.py
│   │   ├── calculate_flops.py
│   │   ├── create_onnx_pipeline.py
│   │   ├── demo.py
│   │   ├── evaluate_fid_lpips.py
│   │   ├── export_inference_model.py
│   │   └── generate_masks.py
│   └── torch_utils/                # PyTorch utilities
├── outputs/                        # Processed outputs
├── uploads/                        # Uploaded files
├── venv/                           # Virtual environment (not in repo)
└── README.md                       # This file
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -m 'Add your feature'`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- U2Net: [Original Paper](https://arxiv.org/abs/2005.09007)
- MiGAN and CoMoDGAN: Custom implementations for object inpainting.
- Built with PyTorch, Flask, and other open-source libraries.

For more information or support, please open an issue on GitHub.
