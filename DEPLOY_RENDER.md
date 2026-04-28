Render deployment instructions

1) Create a new Web Service on Render (https://dashboard.render.com/new)
   - Connect the GitHub repo to Render
   - Build command: `pip install -r requirements.txt`
   - Start command (Procfile exists): `gunicorn app:app --workers 1 --threads 1 --timeout 180`

2) Set environment variables in Render service settings:
   - `HF_API_TOKEN`: Your Hugging Face API token (required)
   - `HF_BG_MODEL`: Hugging Face model id for background removal (e.g. `username/u2net-bg-model`)
   - `HF_OBJ_MODEL`: Hugging Face model id for object inpainting (e.g. `username/migan-inpaint`)
   - `PORT`: (optional) Render sets this automatically

3) Notes:
   - The backend proxies requests to the HF Inference API. Ensure your HF models are configured to accept image inputs or deployed as inference endpoints.
   - Remove any large model weight files from the repository before pushing (e.g., `background/models/u2net.pth`, `object/models/migan_512_places2.pt`).

4) Frontend:
   - Deploy the `frontend/` folder to Vercel as a static site.
   - Update `frontend/js/api-service.js` or set `window.__API_BASE__` to `https://<your-render-service>.onrender.com` so the frontend calls the Render backend.

5) Testing:
   - After both services are deployed, open the frontend and verify image processing works.
   - If you see HF auth errors, verify `HF_API_TOKEN` in Render settings.
