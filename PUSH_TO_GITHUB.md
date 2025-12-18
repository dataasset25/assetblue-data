# How to Push to GitHub

## Step 1: Install Git

Git is not currently installed on your system. You need to install it first:

1. **Download Git for Windows:**
   - Go to: https://git-scm.com/download/win
   - Download the latest version (64-bit installer recommended)

2. **Install Git:**
   - Run the installer
   - Use default settings (recommended)
   - Make sure "Git from the command line and also from 3rd-party software" is selected
   - Complete the installation

3. **Restart PowerShell/Terminal:**
   - Close and reopen PowerShell after installation
   - This ensures Git is added to your PATH

## Step 2: Verify Git Installation

Open PowerShell and run:
```powershell
git --version
```

You should see something like: `git version 2.x.x`

## Step 3: Configure Git (First Time Only)

If this is your first time using Git, configure your name and email:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 4: Navigate to Repository

```powershell
cd C:\Users\DELL\OneDrive\Desktop\assetblue-data
```

## Step 5: Initialize and Push

Run these commands one by one:

```powershell
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Consolidated 4 repositories"

# Add GitHub remote
git remote add origin https://github.com/dataasset25/assetblue-data.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 6: Authentication

When you run `git push`, you may be prompted for authentication:

- **If using HTTPS:** You'll need a Personal Access Token (PAT)
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - Generate a new token with `repo` permissions
  - Use the token as your password when prompted

- **If using SSH:** You'll need to set up SSH keys first

## Alternative: Use GitHub Desktop

If you prefer a graphical interface:

1. Download GitHub Desktop: https://desktop.github.com/
2. Sign in with your GitHub account
3. Click "File" → "Add Local Repository"
4. Select the `assetblue-data` folder
5. Click "Publish repository" to push to GitHub

## Troubleshooting

### "git is not recognized"
- Make sure Git is installed
- Restart PowerShell after installation
- Check if Git is in your PATH: `$env:Path`

### "Authentication failed"
- Use a Personal Access Token instead of password
- Make sure the token has `repo` permissions

### "Repository not found"
- Verify the repository exists on GitHub: https://github.com/dataasset25/assetblue-data
- Check that you have write access to the repository

