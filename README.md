# Pixerase.AI - AI-Powered Image Editing

Pixerase.AI is an advanced AI-powered image editing tool designed for seamless background removal and object inpainting.

Deployment architecture (recommended):

- Frontend: Vercel (static site from `frontend/`)
- Backend: Render (Flask API `/api/*` endpoints in `app.py`)
- Models & inference: Hugging Face (models hosted as Inference API or Endpoints)

This repository contains both the frontend and backend; heavy model weights should be hosted on Hugging Face (or external storage) and not kept inside the repo for deployment.

## 🌟 Features

- **Background Removal**: Automatically detect and remove backgrounds from images using U2Net model
- **Object Inpainting**: Fill in removed objects or areas with contextually appropriate content using MiGAN
- **Unified Interface**: Single Gradio application with dual processing tabs
- **Easy Deployment**: One-click deployment on Hugging Face Spaces
- **Memory Optimized**: CPU and GPU support with intelligent resource management
- **Frontend Integration**: Optional web interface for user redirection to HF Spaces

## 🏗️ Architecture

The application runs as a single **Gradio interface** on Hugging Face Spaces:

```
Hugging Face Spaces (Single Gradio App)
├── Tab 1: Background Removal (U2Net)
├── Tab 2: Object Removal (MiGAN)
└── Shared Model Loading & Processing
```

**Key Components**:
- **Background removal**: U2Net for segmentation + mask refinement
- **Object removal**: MiGAN for inpainting + GrabCut for mask processing
- **Framework**: Gradio for web UI
- **Models**: Hosted on Google Drive with auto-download

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- Virtual environment (venv/conda)

### Local Development

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/pixerase-ai.git
   cd pixerase-ai
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare Models** (choose one):
   - **Option A**: Download models manually
     - U2Net: `background/models/u2net.pth`
     - MiGAN: `object/models/migan_512_places2.pt`
   
   - **Option B**: Auto-download from Google Drive
     - Set `BG_MODEL_FILE_ID` environment variable
     - Set `OBJECT_MODEL_FILE_ID` environment variable

5. **Run Locally**:
   ```bash
   python app.py
   ```
   Access at: `http://localhost:7860`

## 📋 Deployment on Hugging Face Spaces

### Prerequisites
- Hugging Face account
- GitHub repository
- Models hosted on Google Drive (or HF Hub)

### Deployment Steps

**For detailed instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

**Quick Summary**:

1. Create new Space: https://huggingface.co/spaces
   - Select **Gradio** SDK
   - Name: `pixerase-ai`
   
2. Connect GitHub repository or upload files manually

3. Set environment variables in Space Settings:
   ```
   DEPLOYMENT_TARGET=huggingface
   TORCH_THREADS=1
   BG_MODEL_FILE_ID=<your_file_id>
   OBJECT_MODEL_FILE_ID=<your_file_id>
   SKIP_MODEL_DOWNLOAD=false
   ```

4. Select hardware (CPU free, or GPU-T4 paid)

5. Space builds and launches automatically

### Getting Model File IDs from Google Drive

1. Upload models to Google Drive
2. Right-click → Share → Get link
3. Extract ID from URL:
   ```
   https://drive.google.com/file/d/{FILE_ID}/view
   ```
4. Set as environment variables

## 📁 Project Structure

```
pixerase-ai/
├── app.py                      # Main Gradio application
├── requirements.txt            # Python dependencies
├── app.yaml                    # HF Space configuration
├── README.md                   # This file
│
├── DEPLOYMENT_GUIDE.md         # Detailed deployment guide
├── QUICK_START.md              # Quick reference
├── DEPLOYMENT_CHECKLIST.md     # Verification checklist
├── CHANGES.md                  # Migration summary
│
├── background/                 # Background removal module
│   ├── model_loader.py
│   ├── background_removal.py
│   ├── utils.py
│   ├── model/
│   │   └── u2net.py           # U2Net architecture
│   └── models/
│       └── u2net.pth          # Model weights (~168MB)
│
├── object/                     # Object removal module
│   ├── infer.py
│   ├── main.py
│   ├── dnnlib/
│   ├── lib/                   # Supporting utilities
│   ├── torch_utils/
│   ├── model_zoo/
│   └── models/
│       └── migan_512_places2.pt # Model weights (~512MB)
│
├── frontend/                   # Web interface (optional)
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js
│   │   ├── api-service.js     # HF Space redirect
│   │   ├── ui-controller.js
│   │   ├── canvas-manager.js
│   │   └── image-processor.js
│   └── templates/
│       └── index.html
│
└── outputs/                    # Processing output directory
```

## ⚙️ Configuration

### Environment Variables

**Required (HF Spaces)**:
- `DEPLOYMENT_TARGET`: `huggingface` (required)
- `BG_MODEL_FILE_ID`: Google Drive ID for U2Net
- `OBJECT_MODEL_FILE_ID`: Google Drive ID for MiGAN

**Optional**:
- `TORCH_THREADS`: PyTorch threads (default: 1)
- `SKIP_MODEL_DOWNLOAD`: Skip auto-download (default: false)
- `MODELS_DIR`: Model storage location (default: models/)

**Development**:
- `DEPLOYMENT_TARGET`: `development` (optional, for local testing)

## 🤖 Model Information

### Background Removal - U²-Net
- **Task**: Semantic segmentation for background extraction
- **Input**: RGB images (any size)
- **Output**: Foreground mask + composite image
- **Size**: 168 MB
- **Performance**: CPU: 5-15s/image, GPU: <1s/image

### Object Removal - MiGAN
- **Task**: GAN-based image inpainting
- **Input**: RGB image + binary mask (white=remove, black=keep)
- **Output**: Inpainted image
- **Size**: 512 MB
- **Performance**: CPU: 10-30s/image, GPU: 2-5s/image

## 🔧 How It Works

### Background Removal Pipeline
1. User uploads image
2. U2Net generates foreground mask
3. Mask is refined using morphological operations
4. Foreground composited on optional background template
5. Result displayed to user

### Object Removal Pipeline
1. User uploads image and mask
2. GrabCut refines mask based on image content
3. MiGAN inpaints masked regions using learned patterns
4. Result displayed to user

## 📚 Usage Guide

### On Hugging Face Spaces

#### Background Removal Tab
1. Upload an image
2. Optionally select background template
3. Click "Remove Background"
4. Download result

#### Object Removal Tab
1. Upload image to remove from
2. Upload mask image (white = remove, black = keep)
3. Click "Remove Object"
4. Download result

### Optional: Using Frontend

If deploying the frontend separately:
1. Update `api-service.js` with your HF Space URL
2. Frontend will redirect to HF Spaces on processing

## 🐛 Troubleshooting

### Models Not Downloading
- Verify Google Drive file IDs are correct
- Ensure files are public or shared with "Anyone with link"
- Check internet connection
- Look at Space logs for gdown errors

### Out of Memory
- Reduce input image size
- Upgrade to GPU-T4 hardware
- Increase HF Space memory allocation
- Use smaller models (future versions)

### Slow Processing
- **CPU**: 5-30s per image (normal for free tier)
- **GPU-T4**: 2-10s per image
- **Solution**: Upgrade to GPU hardware for faster processing

### Import Errors
- Verify all dependencies in requirements.txt
- Check for missing PyTorch/CUDA compatibility
- Verify model files exist or download correctly
- Check Python version (3.8+ required)

### Build Failures
- Check HF Space build logs
- Verify environment variables are set correctly
- Ensure all files are uploaded
- Check requirements.txt for version conflicts

## 📖 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Quick reference (5 min read)
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Detailed deployment steps (30 min read)
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Verification checklist
- **[CHANGES.md](./CHANGES.md)** - Migration and architecture details
- **[FILE_REFERENCE.md](./FILE_REFERENCE.md)** - File-by-file guide

## 📦 Dependencies

### Core
- `torch>=2.0.0` - Deep learning framework
- `torchvision>=0.15.0` - Computer vision utilities
- `gradio>=4.4.1` - Web UI framework
- `gradio-client>=0.2.0` - Gradio API client
- `pillow>=10.0.0` - Image processing

### Supporting
- `opencv-python>=4.8.0` - Image processing
- `scikit-image>=0.21.0` - Image algorithms
- `gdown>=6.0.0` - Google Drive downloads
- `numpy>=1.24.0` - Numerical computing

See [requirements.txt](./requirements.txt) for complete list.

## 🎯 Performance Notes

### Recommended Settings

**For Free CPU Tier**:
- Max image size: 1024x1024
- Expected time: 10-30s per image
- Concurrent users: 1-2
- Cost: Free

**For GPU-T4 (Recommended)**:
- Max image size: 2048x2048
- Expected time: 2-5s per image
- Concurrent users: 5-10
- Cost: ~$0.50/hour

**For GPU-A100**:
- Max image size: 4096x4096
- Expected time: <1s per image
- Concurrent users: 20+
- Cost: ~$1.00/hour

## 📞 Support & Contribution

### Getting Help
1. Check [Troubleshooting](#-troubleshooting) section
2. Read [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
3. Search existing GitHub issues
4. Open new issue with:
   - Your deployment target (HF/development)
   - Error message and logs
   - Steps to reproduce
   - Python version and OS

### Contributing
- Fork the repository
- Create feature branch (`git checkout -b feature/amazing-feature`)
- Commit changes (`git commit -m 'Add amazing feature'`)
- Push to branch (`git push origin feature/amazing-feature`)
- Open Pull Request

### Reporting Issues
- Use GitHub Issues for bug reports
- Include error logs and reproduction steps
- Specify your environment (OS, Python version, hardware)

## 📜 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- **U²-Net**: [Original Paper](https://arxiv.org/abs/2005.09007)
- **MiGAN**: [GitHub Repository](https://github.com/Picsart-AI-Research/MI-GAN)
- **Gradio**: [Framework](https://gradio.app)
- **Hugging Face**: [Spaces Platform](https://huggingface.co/spaces)

## 📝 Citation

If you use this project, please cite:

```bibtex
@project{pixerase2024,
  title={Pixerase.AI - AI-Powered Image Editing},
  author={Your Name},
  year={2024},
  url={https://github.com/your-username/pixerase-ai}
}
```

## 📊 Project Statistics

- **Models**: 2 (U2Net, MiGAN)
- **Supported Tasks**: Background removal, Object inpainting
- **Deployment Platform**: Hugging Face Spaces
- **Framework**: Gradio, PyTorch
- **Python Version**: 3.8+
- **License**: Educational/Research

## 🔮 Future Enhancements

- [ ] More inpainting models
- [ ] Batch processing support
- [ ] Real-time video processing
- [ ] Model quantization for faster inference
- [ ] Advanced mask editor in Gradio
- [ ] API endpoint documentation
- [ ] Mobile-friendly interface
- [ ] Custom model fine-tuning

---

**Last Updated**: April 27, 2026  
**Status**: Production Ready ✅  
**Deployed On**: Hugging Face Spaces
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
