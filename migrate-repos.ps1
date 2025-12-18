# PowerShell script to migrate 4 repositories into assetblue-data
# Run this script from the assetblue-data directory

Write-Host "=== Repository Migration Script ===" -ForegroundColor Green
Write-Host ""

$repos = @(
    @{Name="Boiler_Data_Tool"; Folder="Boiler_Data_Tool"; URL="https://github.com/dataasset25/Boiler_Data_Tool.git"},
    @{Name="simple_pipeline"; Folder="simple_pipeline"; URL="https://github.com/dataasset25/simple_pipeline.git"},
    @{Name="assets-model-parallel"; Folder="assets-model-parallel"; URL="https://github.com/dataasset25/assets-model-parallel.git"},
    @{Name="asset-boiler"; Folder="asset-boiler"; URL="https://github.com/dataasset25/asset-boiler.git"}
)

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Clone each repository into its respective folder"
Write-Host "  2. Remove .git folders from subfolders"
Write-Host "  3. Initialize a new git repository in the root"
Write-Host ""
$confirm = Read-Host "Do you want to continue? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Migration cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Starting migration..." -ForegroundColor Green
Write-Host ""

# Clone each repository
foreach ($repo in $repos) {
    Write-Host "Cloning $($repo.Name)..." -ForegroundColor Cyan
    
    if (Test-Path $repo.Folder) {
        $overwrite = Read-Host "Folder $($repo.Folder) already exists. Overwrite? (Y/N)"
        if ($overwrite -eq "Y" -or $overwrite -eq "y") {
            Remove-Item -Path $repo.Folder -Recurse -Force
        } else {
            Write-Host "Skipping $($repo.Name)..." -ForegroundColor Yellow
            continue
        }
    }
    
    try {
        git clone $repo.URL $repo.Folder
        Write-Host "  ✓ Successfully cloned $($repo.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to clone $($repo.Name): $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Removing .git folders from subfolders..." -ForegroundColor Cyan

# Remove .git folders from each subfolder
foreach ($repo in $repos) {
    $gitFolder = Join-Path $repo.Folder ".git"
    if (Test-Path $gitFolder) {
        Remove-Item -Path $gitFolder -Recurse -Force
        Write-Host "  ✓ Removed .git from $($repo.Folder)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Initializing new git repository..." -ForegroundColor Cyan

# Initialize new git repository if not already initialized
if (-not (Test-Path ".git")) {
    git init
    Write-Host "  ✓ Initialized new git repository" -ForegroundColor Green
} else {
    Write-Host "  ℹ Git repository already initialized" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Migration Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the migrated content in each folder"
Write-Host "  2. Update any paths or references if needed"
Write-Host "  3. Add and commit files: git add ."
Write-Host "  4. Create the repository on GitHub: assetblue-data"
Write-Host "  5. Push to GitHub: git remote add origin <your-repo-url>"
Write-Host "                     git push -u origin main"

