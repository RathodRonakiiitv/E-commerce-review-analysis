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
        - `DATABASE_URL`: Add this manually in Render using your external PostgreSQL provider (Neon, Supabase, Railway, Aiven, etc.).
            - Example: `postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require`
            - `postgres://...` URLs are also accepted by the backend and normalized automatically.
            - Avoid SQLite on Render free tier because filesystem data is not persistent.
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

-   **PowerShell Execution Policy Error**: If you see `File ...npx.ps1 cannot be loaded`, use `cmd /c` before the command:
    ```powershell
    cmd /c npx vercel login
    cmd /c npx vercel --prod
    ```
    Or run this once in PowerShell as Administrator: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Migrating From Expiring Render DB

If your current Render PostgreSQL instance is expiring, migrate data before shutdown.

1.  Export old database (from your machine with `pg_dump` installed):
    ```powershell
    pg_dump "OLD_RENDER_DATABASE_URL" -Fc -f review_analyzer_backup.dump
    ```
2.  Create a new PostgreSQL database on your target provider.
3.  Import data into the new database:
    ```powershell
    pg_restore --no-owner --no-privileges -d "NEW_DATABASE_URL" review_analyzer_backup.dump
    ```
4.  In Render -> your backend service -> **Environment**, update `DATABASE_URL` to the new URL.
5.  Trigger a deploy and verify the API health endpoint and product analysis flow.
