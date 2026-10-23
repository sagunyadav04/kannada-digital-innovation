# Deploying (Docker is required: Tesseract Kannada data needs apt packages)

## Option A: Render (easiest)
1. Push the repo to GitHub.
2. Render → New → Web Service → pick the repo. It reads `render.yaml` / the Dockerfile.
3. Add env var `GEMINI_API_KEY` (free key from https://aistudio.google.com/apikey).
4. Deploy; open `https://<name>.onrender.com/api/health` to confirm `{"ok": true, "ai": true}`.
Free instances sleep when idle: open the site a minute before judging time, and keep it up until results.

## Option B: Hugging Face Spaces (no sleep on free CPU)
New Space → SDK: Docker. Push the repo. Add a README front-matter line `app_port: 8000` and set `GEMINI_API_KEY` under Settings → Secrets.

## Notes
- Free hosts have ephemeral disk: saved library entries may reset on redeploy. Fine for a demo.
- Never commit `.env`. Only `.env.example` is in the repo.
