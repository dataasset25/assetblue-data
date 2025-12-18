# PowerShell script to clone 4 repositories into assetblue-data folders
# This uses git clone for a cleaner migration

Write-Host "=== Clone Repositories Script ===" -ForegroundColor Green
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
    exit 1
}

Write-Host ""

$repos = @(
    @{Name="Boiler_Data_Tool"; Folder="Boiler_Data_Tool"; URL="https://github.com/dataasset25/Boiler_Data_Tool.git"},
    @{Name="simple_pipeline"; Folder="simple_pipeline"; URL="https://github.com/dataasset25/simple_pipeline.git"},
    @{Name="assets-model-parallel"; Folder="assets-model-parallel"; URL="https://github.com/dataasset25/assets-model-parallel.git"},
    @{Name="asset-boiler"; Folder="asset-boiler"; URL="https://github.com/dataasset25/asset-boiler.git"}
)

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Clone each repository into its respective folder"
Write-Host "  2. Remove .git folders to prepare for consolidation"
Write-Host "  3. Keep all code files"
Write-Host ""

$confirm = Read-Host "Do you want to continue? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Starting clone operation..." -ForegroundColor Green
Write-Host ""

foreach ($repo in $repos) {
    Write-Host "Processing $($repo.Name)..." -ForegroundColor Cyan
    
    # Check if folder already exists
    if (Test-Path $repo.Folder) {
        $overwrite = Read-Host "  Folder $($repo.Folder) already exists. Overwrite? (Y/N)"
        if ($overwrite -eq "Y" -or $overwrite -eq "y") {
            Write-Host "  Removing existing folder..." -ForegroundColor Gray
            Remove-Item -Path $repo.Folder -Recurse -Force
        } else {
            Write-Host "  Skipping $($repo.Name)..." -ForegroundColor Yellow
            continue
        }
    }
    
    # Clone the repository
    try {
        Write-Host "  Cloning from GitHub..." -ForegroundColor Gray
        git clone $repo.URL $repo.Folder
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Successfully cloned $($repo.Name)" -ForegroundColor Green
            
            # Remove .git folder to prepare for consolidation
            $gitFolder = Join-Path $repo.Folder ".git"
            if (Test-Path $gitFolder) {
                Write-Host "  Removing .git folder..." -ForegroundColor Gray
                Remove-Item -Path $gitFolder -Recurse -Force
                Write-Host "  [OK] Ready for consolidation" -ForegroundColor Green
            }
        } else {
            Write-Host "  [ERROR] Failed to clone $($repo.Name)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] Exception: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=== Clone Operation Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "All repositories have been cloned into their respective folders." -ForegroundColor Yellow
Write-Host "The .git folders have been removed to prepare for consolidation." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review the cloned content in each folder"
Write-Host "  2. Initialize the main repository:"
Write-Host "     git init"
Write-Host "     git add ."
Write-Host "     git commit -m 'Initial commit: Consolidated 4 repositories'"
Write-Host "  3. Push to GitHub:"
Write-Host "     git remote add origin https://github.com/dataasset25/assetblue-data.git"
Write-Host "     git branch -M main"
Write-Host "     git push -u origin main"

