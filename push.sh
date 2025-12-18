#!/bin/bash
# Bash script to push assetblue-data to GitHub
# Run this in Git Bash (MINGW64)

echo "=== Push to GitHub Script ==="
echo ""

# Navigate to repository directory
cd /c/Users/DELL/OneDrive/Desktop/assetblue-data

# Check if already a git repository
if [ -d ".git" ]; then
    echo "Git repository already initialized"
    git status
else
    echo "Initializing git repository..."
    git init
fi

echo ""
echo "Adding all files..."
git add .

echo ""
echo "Creating commit..."
git commit -m "Initial commit: Consolidated 4 repositories"

echo ""
echo "Checking remote..."
if git remote get-url origin &>/dev/null; then
    echo "Remote already configured: $(git remote get-url origin)"
else
    echo "Adding remote origin..."
    git remote add origin https://github.com/dataasset25/assetblue-data.git
fi

echo ""
echo "Setting main branch..."
git branch -M main

echo ""
echo "=== Ready to Push ==="
echo ""
echo "Run this command to push to GitHub:"
echo "  git push -u origin main"
echo ""
echo "Note: You will be prompted for GitHub credentials."
echo "      Username: dataasset25"
echo "      Password: Use a Personal Access Token (PAT)"
echo ""
echo "To create a PAT:"
echo "  1. Go to: https://github.com/settings/tokens"
echo "  2. Generate new token (classic)"
echo "  3. Select 'repo' permissions"
echo "  4. Copy and use the token as password"
echo ""

read -p "Do you want to push now? (Y/N): " push
if [ "$push" = "Y" ] || [ "$push" = "y" ]; then
    echo ""
    echo "Pushing to GitHub..."
    git push -u origin main
    if [ $? -eq 0 ]; then
        echo ""
        echo "=== SUCCESS! ==="
        echo "Repository pushed to: https://github.com/dataasset25/assetblue-data"
    else
        echo ""
        echo "Push failed. Check the error message above."
    fi
else
    echo ""
    echo "Skipped push. Run 'git push -u origin main' when ready."
fi

