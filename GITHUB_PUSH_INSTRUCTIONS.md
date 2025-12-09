# How to Push Sanjeevani To GitHub

I have already initialized a local Git repository for you. To push this to GitHub, follow these steps:

1.  **Create a New Repository on GitHub**:
    *   Go to [github.com/new](https://github.com/new).
    *   Name it `sanjeevani-agent` (or whatever you prefer).
    *   **Do not** initialize with README, .gitignore, or License (we already have them).
    *   Click **Create repository**.

2.  **Link your Local Repo**:
    *   Copy the URL of your new repository (e.g., `https://github.com/YourUsername/sanjeevani-agent.git`).
    *   Open your terminal in VS Code (Ctrl+`).
    *   Run the following commands:

```powershell
git remote add origin <PASTE_YOUR_REPO_URL_HERE>
git branch -M main
git push -u origin main
```

3.  **Authentication**:
    *   If asked for credentials, a browser window should pop up to let you sign in. 
    *   If you enabled 2FA, you might need a Personal Access Token if password auth fails.

That's it! Your code is now live on GitHub.
