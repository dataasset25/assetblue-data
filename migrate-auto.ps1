# PowerShell script to download and migrate 4 repositories into assetblue-data
# Auto-run version (no user prompts)

Write-Host "=== Repository Migration Script (Auto-Run) ===" -ForegroundColor Green
Write-Host ""

$repos = @(
    @{Name="Boiler_Data_Tool"; Folder="Boiler_Data_Tool"; URL="https://github.com/dataasset25/Boiler_Data_Tool/archive/refs/heads/main.zip"},
    @{Name="simple_pipeline"; Folder="simple_pipeline"; URL="https://github.com/dataasset25/simple_pipeline/archive/refs/heads/main.zip"},
    @{Name="assets-model-parallel"; Folder="assets-model-parallel"; URL="https://github.com/dataasset25/assets-model-parallel/archive/refs/heads/main.zip"},
    @{Name="asset-boiler"; Folder="asset-boiler"; URL="https://github.com/dataasset25/asset-boiler/archive/refs/heads/main.zip"}
)

$tempDir = Join-Path $PSScriptRoot "temp_downloads"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

Write-Host "Starting download and migration..." -ForegroundColor Green
Write-Host ""

foreach ($repo in $repos) {
    Write-Host "Processing $($repo.Name)..." -ForegroundColor Cyan
    
    $zipPath = Join-Path $tempDir "$($repo.Name).zip"
    $extractPath = Join-Path $tempDir $repo.Name
    
    # Download the repository
    try {
        Write-Host "  Downloading from GitHub..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $repo.URL -OutFile $zipPath -UseBasicParsing
        Write-Host "  [OK] Downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to download: $_" -ForegroundColor Red
        continue
    }
    
    # Extract the ZIP file
    try {
        Write-Host "  Extracting files..." -ForegroundColor Gray
        Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
        
        # Find the extracted folder (usually has -main suffix)
        $extractedFolder = Get-ChildItem -Path $extractPath -Directory | Select-Object -First 1
        
        if ($extractedFolder) {
            # Clear target folder if it exists (auto-overwrite)
            if (Test-Path $repo.Folder) {
                Write-Host "  Removing existing folder..." -ForegroundColor Gray
                Remove-Item -Path $repo.Folder -Recurse -Force
            }
            
            # Copy all files from extracted folder to target folder
            Write-Host "  Copying files to $($repo.Folder)..." -ForegroundColor Gray
            New-Item -ItemType Directory -Path $repo.Folder -Force | Out-Null
            Copy-Item -Path "$($extractedFolder.FullName)\*" -Destination $repo.Folder -Recurse -Force
            
            Write-Host "  [OK] Successfully migrated $($repo.Name)" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Could not find extracted folder" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] Failed to extract: $_" -ForegroundColor Red
    }
}

# Clean up temporary files
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Cyan
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] Cleanup complete" -ForegroundColor Green

Write-Host ""
Write-Host "=== Migration Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "All 4 repositories have been migrated into their respective folders." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps to push to GitHub:" -ForegroundColor Yellow
Write-Host "  1. Install Git from https://git-scm.com/download/win (if not installed)"
Write-Host "  2. Open PowerShell in this directory and run:"
Write-Host "     git init"
Write-Host "     git add ."
Write-Host "     git commit -m 'Initial commit: Consolidated 4 repositories'"
Write-Host "     git remote add origin https://github.com/dataasset25/assetblue-data.git"
Write-Host "     git branch -M main"
Write-Host "     git push -u origin main"

