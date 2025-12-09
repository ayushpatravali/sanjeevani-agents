# ☁️ Streamlit Cloud Deployment Guide

This guide explains how to deploy your app and securely handle your Env variables (Secrets).

## Step 1: Push to GitHub (Already Done)
You have already pushed your code to GitHub. 🎉

## Step 2: Sign up for Weaviate Cloud (WCS)
Since your app is in the cloud, it needs a database in the cloud.
1.  Go to [Weaviate Cloud Services](https://console.weaviate.cloud/).
2.  Sign up (Free).
3.  Click **Create Cluster** (Free Sandbox).
4.  Once created, click **Details**.
5.  Copy the **Cluster URL** (e.g., `https://my-sandbox-123.weaviate.network`).
6.  Copy the **API Key** (under API keys).

## Step 3: Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Sign in with GitHub.
3.  Click **New app**.
4.  **Repository**: Select `sanjeevani-agents`.
5.  **Branch**: `main`.
6.  **Main file path**: `app.py`.
7.  **Click "Advanced settings"** (This is crucial!).

## Step 4: Configure Secrets (Environment Variables)
In the "Advanced settings" -> **Secrets** text box, paste the following (replace with your REAL keys from Step 2):

```toml
# Copy-paste this into the Streamlit Secrets box
WEAVIATE_URL = "https://your-weaviate-cluster-url.weaviate.network"
WEAVIATE_API_KEY = "your-weaviate-api-key"
GROQ_API_KEY = "your-groq-api-key"
ENVIRONMENT = "production"
```

> **Note**: Streamlit automatically loads these secrets into your app's environment variables (`os.getenv`). You do **not** need to push a `.env` file to GitHub.

## Step 6: Migrate Data to Cloud
Currently, your app is running on Streamlit Cloud, but it's connected to an **EMPTY** database in the cloud. You need to upload your local data to Weaviate Cloud.

1.  **Open your `.env` file locally**.
2.  Update `WEAVIATE_URL` and `WEAVIATE_API_KEY` with the Cloud credentials (from Step 2).
3.  Run the migration script:
    ```powershell
    python src/scripts/ingest_to_cloud.py
    ```
4.  Wait for it to finish ("✅ Ingestion Complete").
5.  Now your Streamlit App will work!

---

## ❓ Common Questions

**Q: Streamlit says "Error connecting to Weaviate: timed out"**
**A:** This means your app is trying to connect to `localhost` (your laptop) from the cloud. You missed **Step 4** (setting Secrets) or your Secrets are wrong. Make sure `WEAVIATE_URL` starts with `https://` and points to `.weaviate.network`, not `localhost`.

**Q: "How to enable env config in git?"**
**A:** You **don't**. You never push `.env` to Git because it contains passwords. Instead, you use the "Secrets" dashboard on the hosting platform (Streamlit Cloud, Vercel, AWS, etc.) to set them securely.

**Q: What about `packages.txt`?**
**A:** I already created this file for you. Streamlit Cloud usually reads it automatically to install the microphone tools (`portaudio`).
