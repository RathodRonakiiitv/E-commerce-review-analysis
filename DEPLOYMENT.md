# Deployment Guide

This guide explains how to deploy the **E-commerce Review Analysis** application.
The application consists of a **Python Backend (FastAPI)** and a **React Frontend (Vite)**.

## Prerequisites

- [GitHub Account](https://github.com)
- [Render Account](https://render.com) (for Backend)
- [Vercel Account](https://vercel.com) (for Frontend)
- [Groq API Key](https://console.groq.com)

---

## Step 1: Deploy Backend (Render)

Because the backend uses heavy ML libraries (PyTorch, Transformers), it requires a containerized environment. Render provides a free tier that supports Docker.

1.  **Push your code to GitHub** (if not already done).
2.  **Log in to Render** and click **New +** -> **Web Service**.
3.  Connect your GitHub repository.
4.  Render should automatically detect the `render.yaml` file in the root directory.
    - If prompted, select the **Free** plan.
5.  **Environment Variables**:
    - `GROQ_API_KEY`: Add your actual Groq API Key.
    - `CORS_ORIGINS`: Update this later with your Vercel URL (e.g., `https://your-app.vercel.app`). For now, you can leave the default or add `*` for testing (not recommended for production).
    - `DATABASE_URL`: Render will automatically set this if you add a Database, or it will use SQLite (temporary file system) if you don't.
      - **Note**: The **Free Tier** on Render refreshes the filesystem on restart, so SQLite data will be lost. For persistence, create a **Render PostgreSQL** database and link it (Render usually prompts for this if using `render.yaml`).
6.  **Deploy**: Click **Create Web Service**.
    - The build may take 5-10 minutes due to ML dependencies.
7.  **Copy the Backend URL**: Once deployed, copy the URL (e.g., `https://review-analyzer-backend.onrender.com`).

---

## Step 2: Deploy Frontend (Vercel)

1.  **Log in to Vercel** and click **Add New** -> **Project**.
2.  Import your GitHub repository.
3.  **Configure Project**:
    - **Framework Preset**: Vite
    - **Root Directory**: Click `Edit` and select `frontend`.
4.  **Environment Variables**:
    - Add a new variable:
      - **Name**: `VITE_API_URL`
      - **Value**: The Backend URL from Step 1 (e.g., `https://review-analyzer-backend.onrender.com`).
      - **Important**: Do **not** include the trailing `/api` (the app appends it automatically) or trailing slash `/`.
5.  **Deploy**: Click **Deploy**.
6.  Wait for the build to finish.

---

## Step 3: Final Configuration

1.  **Update CORS**:
    - Go back to your **Render Dashboard** -> **Environment**.
    - specific your **Frontend URL** (e.g., `https://your-project.vercel.app`) to the `CORS_ORIGINS` variable (comma-separated if multiple).
    - Redeploy the backend (Manual Deploy -> Deploy latest commit) if necessary.

2.  **Access App**:
    - Open your Vercel URL.
    - Try analyzing a product to verify connectivity.

## Troubleshooting

-   **Backend Memory Issues**: The ML models (DistilBERT) are heavy. If the Render Free tier (512MB RAM) crashes, try simpler models or upgrade to a paid plan.
-   **CORS Errors**: Ensure `CORS_ORIGINS` in Render exactly matches your Vercel URL (no trailing slash usually, or check browser console for the exact Origin header sent).
-   **Database**: If reviews disappear after a while, it's because SQLite on Render Free tier is ephemeral. Use PostgreSQL for persistence.
