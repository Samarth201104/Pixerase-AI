# Pixerase-AI

Pixerase-AI is an advanced AI-powered image editing tool designed for seamless background removal and object inpainting. Leveraging state-of-the-art deep learning models like U2Net and custom GAN-based architectures (e.g., MiGAN, CoMoDGAN), it provides users with an intuitive web interface to process images efficiently. Whether you're removing backgrounds for product photos or inpainting objects in scenes, Pixerase-AI delivers high-quality results with minimal effort.

## Features

- **Background Removal**: Automatically detect and remove backgrounds from images using U2Net model.
- **Object Inpainting**: Fill in removed objects or areas with contextually appropriate content using GAN models like MiGAN and CoMoDGAN.
- **Web Interface**: User-friendly frontend built with HTML, CSS, and JavaScript for easy image upload and processing.
- **Batch Processing**: Support for processing multiple images via scripts.
- **Model Flexibility**: Pre-trained models for various datasets (FFHQ, Places2) and resolutions (256x256, 512x512).
- **Evaluation Tools**: Built-in scripts for evaluating model performance (FID, LPIPS, PSNR, SSIM).
- **Export Options**: Export processed images and create ONNX pipelines for deployment.

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)
- A virtual environment tool (e.g., venv)

### Steps

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
   *Note: requirements.txt contains the exact package versions as installed in the development environment (generated via `pip freeze`).*

4. **Download Pre-trained Models**:
   - Download the required model files and place them in the appropriate directories:
     - U²-Net model (`u2net.pth`) → `background/models/`
     - MI-GAN models (e.g., `migan_512_places2.pt`) → `object/models/`
   - Ensure the models match the configurations in `object/configs/`.

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
