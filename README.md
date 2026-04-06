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
   - Place the required model files (e.g., `u2net.pth`, `migan_512_places2.pt`) in the `models/` directory.
   - Ensure the models match the configurations in `configs/`.

   ### 🔹 MI-GAN (Object Removal - Inpainting)
   Download from:
   https://drive.google.com/drive/folders/1xNtvN2lto0p5yFKOEEg9RioMjGrYM74w

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
  python scripts/app_autoremoval.py --input path/to/image.jpg --output path/to/output.jpg
  ```

- **Object Inpainting**:
  ```bash
  python object/main.py --config configs/experiment/comodgan_places256.yaml --input path/to/image.jpg --mask path/to/mask.jpg --output path/to/output.jpg
  ```

- **Evaluation**:
  ```bash
  python scripts/evaluate_fid_lpips.py --real_dir path/to/real_images --fake_dir path/to/generated_images
  ```

- **Export to ONNX**:
  ```bash
  python scripts/create_onnx_pipeline.py --model_path models/u2net.pth --output_path outputs/u2net.onnx
  ```

### Configuration

- Modify experiment configurations in `configs/experiment/`.
- Adjust model settings in `configs/model/`.
- Dataset configurations are in `configs/dataset/`.

## Project Structure

```
pixerase-ai/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── background/                     # Background removal module
│   ├── background_removal.py
│   ├── model_loader.py
│   └── utils.py
├── model/                          # U2Net model implementation
├── models/                         # Pre-trained model weights
├── frontend/                       # Web interface
│   ├── css/
│   ├── js/
│   └── templates/
├── object/                         # Object inpainting module
│   ├── infer.py
│   ├── main.py
│   ├── configs/
│   ├── lib/
│   └── scripts/
├── scripts/                        # Utility scripts
├── outputs/                        # Processed outputs
├── uploads/                        # Uploaded files
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
