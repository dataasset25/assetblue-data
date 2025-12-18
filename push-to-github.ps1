# PowerShell script to push assetblue-data to GitHub
# Make sure Git is installed before running this script

Write-Host "=== Push to GitHub Script ===" -ForegroundColor Green
Write-Host ""

# Check if Git is installed
try {
    $gitVersion = git --version 2>&1
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git first:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://git-scm.com/download/win" -ForegroundColor Cyan
    Write-Host "  2. Install with default settings" -ForegroundColor Cyan
    Write-Host "  3. Restart PowerShell" -ForegroundColor Cyan
    Write-Host "  4. Run this script again" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or see PUSH_TO_GITHUB.md for detailed instructions" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Check if already a git repository
if (Test-Path ".git") {
    Write-Host "Git repository already initialized" -ForegroundColor Yellow
    $status = git status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $status -ForegroundColor Gray
    }
} else {
    Write-Host "Initializing git repository..." -ForegroundColor Cyan
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to initialize git repository" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Adding all files..." -ForegroundColor Cyan
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to add files" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m "Initial commit: Consolidated 4 repositories"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Commit failed or no changes to commit" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Checking remote..." -ForegroundColor Cyan
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding remote origin..." -ForegroundColor Cyan
    git remote add origin https://github.com/dataasset25/assetblue-data.git
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to add remote" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Remote already configured: $remote" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setting main branch..." -ForegroundColor Cyan
git branch -M main
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Branch rename failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Ready to Push ===" -ForegroundColor Green
Write-Host ""
Write-Host "Run this command to push to GitHub:" -ForegroundColor Yellow
Write-Host "  git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: You may be prompted for GitHub credentials." -ForegroundColor Gray
Write-Host "      Use a Personal Access Token (PAT) as your password." -ForegroundColor Gray
Write-Host ""
Write-Host "To create a PAT:" -ForegroundColor Yellow
Write-Host "  1. Go to: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "  2. Generate new token (classic)" -ForegroundColor Cyan
Write-Host "  3. Select 'repo' permissions" -ForegroundColor Cyan
Write-Host "  4. Copy and use the token as password" -ForegroundColor Cyan
Write-Host ""

$push = Read-Host "Do you want to push now? (Y/N)"
if ($push -eq "Y" -or $push -eq "y") {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== SUCCESS! ===" -ForegroundColor Green
        Write-Host "Repository pushed to: https://github.com/dataasset25/assetblue-data" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Push failed. Check the error message above." -ForegroundColor Red
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "  - Authentication failed (use PAT token)" -ForegroundColor Gray
        Write-Host "  - Repository doesn't exist on GitHub" -ForegroundColor Gray
        Write-Host "  - No write permissions" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "Skipped push. Run 'git push -u origin main' when ready." -ForegroundColor Yellow
}

