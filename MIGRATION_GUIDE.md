# Migration Guide: Consolidating 4 Repositories into assetblue-data

This guide explains how to migrate content from the 4 separate repositories into this consolidated repository.

## Repositories to Migrate

1. **Boiler_Data_Tool** → `./Boiler_Data_Tool/`
2. **simple_pipeline** → `./simple_pipeline/`
3. **assets-model-parallel** → `./assets-model-parallel/`
4. **asset-boiler** → `./asset-boiler/`

## Migration Steps

### Option 1: Using Git (Recommended)

If you have Git installed and the repositories are on GitHub:

```bash
# Clone each repository into its respective folder
git clone https://github.com/dataasset25/Boiler_Data_Tool.git Boiler_Data_Tool
git clone https://github.com/dataasset25/simple_pipeline.git simple_pipeline
git clone https://github.com/dataasset25/assets-model-parallel.git assets-model-parallel
git clone https://github.com/dataasset25/asset-boiler.git asset-boiler

# Remove .git folders from each subfolder (we'll have one main .git)
cd Boiler_Data_Tool && rm -rf .git && cd ..
cd simple_pipeline && rm -rf .git && cd ..
cd assets-model-parallel && rm -rf .git && cd ..
cd asset-boiler && rm -rf .git && cd ..

# Initialize new git repository for assetblue-data
git init
git add .
git commit -m "Initial commit: Consolidated 4 repositories"
```

### Option 2: Manual Copy

1. Download or clone each repository separately
2. Copy all files from each repository into its corresponding folder:
   - Copy `Boiler_Data_Tool` files → `./Boiler_Data_Tool/`
   - Copy `simple_pipeline` files → `./simple_pipeline/`
   - Copy `assets-model-parallel` files → `./assets-model-parallel/`
   - Copy `asset-boiler` files → `./asset-boiler/`

3. Remove any `.git` folders from the subfolders
4. Initialize a new git repository in the root `assetblue-data` folder

### Option 3: Using GitHub CLI (gh)

```bash
# Install GitHub CLI if not already installed
# Then clone each repo
gh repo clone dataasset25/Boiler_Data_Tool Boiler_Data_Tool
gh repo clone dataasset25/simple_pipeline simple_pipeline
gh repo clone dataasset25/assets-model-parallel assets-model-parallel
gh repo clone dataasset25/asset-boiler asset-boiler

# Remove .git folders and initialize new repo
# (Same as Option 1)
```

## After Migration

1. Update each folder's README.md to reflect the new structure
2. Update any import paths or references that might be affected
3. Test each project to ensure it still works in the new structure
4. Create the new repository on GitHub: `assetblue-data`
5. Push the consolidated repository

## Notes

- Each folder maintains its own project structure and dependencies
- Update any absolute paths or references that might break
- Consider updating documentation to reflect the new consolidated structure

