# How to Upload to GitHub

## Step 1: Initialize Git Repository

```bash
git init
```

## Step 2: Check What Will Be Uploaded

```bash
git status
```

This will show all the files that will be tracked. You should see:
- ✅ Python scripts (.py)
- ✅ README.md files
- ✅ .gitignore
- ✅ requirements.txt
- ✅ Batch files (.bat)
- ❌ No data files (.csv, .json, .pdf, .mp4, etc.)

## Step 3: Add Files to Git

```bash
git add .
```

## Step 4: Make Your First Commit

```bash
git commit -m "Initial commit: Add boiler data collection tools"
```

## Step 5: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click the "+" icon in the top right
3. Select "New repository"
4. Name it (e.g., "boiler-data-tools")
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

## Step 6: Connect and Push

GitHub will show you commands. Use these:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin main
```

Replace:
- `YOUR-USERNAME` with your GitHub username
- `YOUR-REPO-NAME` with your repository name

## Step 7: Verify Upload

Visit your repository on GitHub and verify:
- ✅ All Python scripts are there
- ✅ README.md is there
- ✅ No large data files (PDFs, videos, etc.)

## What Gets Uploaded?

### ✅ Uploaded (Code Only):
- `boiler_images/collect_bing_image_urls_per_boiler_v2.py`
- `searxng/*.py` (all Python scripts)
- `youtube/*.py` (all Python scripts)
- `youtube/*.bat` (setup scripts)
- `README.md`
- `.gitignore`

### ❌ NOT Uploaded (Data Files):
- PDFs
- Videos (.mp4)
- Images (.jpg, .png)
- CSV files
- JSON data files
- Text files with URLs
- Downloaded content

## Troubleshooting

### If you see large files being tracked:
```bash
git status
```
Check the output. If you see data files, make sure your `.gitignore` is correct.

### If you need to remove files from tracking:
```bash
git rm --cached <filename>
git commit -m "Remove data files"
```

### Need help?
All commands are run in PowerShell or Command Prompt from the `E:\work` directory.

