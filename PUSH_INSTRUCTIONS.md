# Push to GitHub - Step by Step Instructions

## Option A: Using Git Bash (MINGW64) - Recommended

Since you have Git Bash open, use these commands:

```bash
# Navigate to the repository
cd /c/Users/DELL/OneDrive/Desktop/assetblue-data

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

## Option B: Using PowerShell (After Restart)

If you want to use PowerShell:

1. **Close and restart PowerShell** (to refresh PATH)
2. Then run:
```powershell
cd C:\Users\DELL\OneDrive\Desktop\assetblue-data
.\push-to-github.ps1
```

Or manually:
```powershell
cd C:\Users\DELL\OneDrive\Desktop\assetblue-data
git init
git add .
git commit -m "Initial commit: Consolidated 4 repositories"
git remote add origin https://github.com/dataasset25/assetblue-data.git
git branch -M main
git push -u origin main
```

## Authentication

When you run `git push`, you'll be prompted for credentials:

- **Username:** Your GitHub username (`dataasset25`)
- **Password:** Use a **Personal Access Token (PAT)**, NOT your GitHub password

### How to Create a Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "assetblue-data"
4. Select scope: Check `repo` (this gives full repository access)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)
7. Use this token as your password when prompted

## Troubleshooting

### "git: command not found"
- Make sure Git is installed
- Restart your terminal/PowerShell
- In Git Bash, Git should always work

### "Authentication failed"
- Make sure you're using a Personal Access Token, not your password
- Check that the token has `repo` permissions

### "Repository not found"
- Verify the repository exists: https://github.com/dataasset25/assetblue-data
- Make sure you have write access

### "Remote origin already exists"
- Remove it first: `git remote remove origin`
- Then add again: `git remote add origin https://github.com/dataasset25/assetblue-data.git`

