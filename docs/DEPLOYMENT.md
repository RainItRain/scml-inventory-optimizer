# Deployment Guide

The app is a **single Docker container**: FastAPI serves the REST API *and* the
compiled React frontend on one port. That makes it a one-URL deploy on any
container host. Two free options are documented below.

The container reads the port from `$PORT` (default `7860`).

---

## Option A — Render (recommended, free)

1. Push this repo to GitHub (see the main README / project setup).
2. Go to <https://dashboard.render.com> → **New +** → **Web Service**.
3. Connect your GitHub account and pick the `scml-inventory-optimizer` repo.
4. Render auto-detects `render.yaml`. Confirm:
   - **Runtime:** Docker
   - **Plan:** Free
   - **Health check path:** `/api/health`
5. Click **Create Web Service**. First build takes ~3–5 min.
6. Your live URL will be `https://scml-inventory-optimizer.onrender.com`
   (or similar). Put it in the README and your résumé.

> Free Render services sleep after ~15 min idle and take ~30s to wake on the next
> request. Fine for a portfolio demo.

---

## Option B — Hugging Face Spaces (free, great for ML demos)

1. Create a Space at <https://huggingface.co/new-space>:
   - **SDK:** Docker → *Blank*
   - **Space hardware:** CPU basic (free)
2. In the Space's **Files**, add a `README.md` header (HF reads this frontmatter):

   ```yaml
   ---
   title: SupplyIQ Inventory Optimizer
   emoji: 📦
   colorFrom: blue
   colorTo: purple
   sdk: docker
   app_port: 7860
   ---
   ```

3. Push this repository's contents to the Space's git remote:

   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/supplyiq
   git push space main
   ```

4. HF builds the Dockerfile automatically and serves it at
   `https://<your-username>-supplyiq.hf.space`.

---

## Option C — Split deploy (Vercel frontend + Render backend)

If you prefer a separate frontend:

1. **Backend on Render** as above, note its URL (e.g. `https://…onrender.com`).
2. **Frontend on Vercel:**
   - Import the repo, set **Root Directory** = `frontend`.
   - Build command `npm run build`, output `dist`.
   - Add a rewrite so `/api/*` proxies to the backend. Create `frontend/vercel.json`:

     ```json
     {
       "rewrites": [
         { "source": "/api/:path*", "destination": "https://YOUR-BACKEND.onrender.com/api/:path*" }
       ]
     }
     ```

The single-container option (A or B) is simpler and recommended.

---

## After deploying

- Update the **Live demo** link in `README.md`.
- Update the project URL in your résumé.
- Optionally enable the free UptimeRobot ping on `/api/health` to keep a Render
  free service warm.
