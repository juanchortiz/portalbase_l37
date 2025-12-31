# GitHub Setup Guide

## ✅ Security Checklist (COMPLETE!)

All API keys have been secured! Here's what was done:

### 1. ✅ Created `config.py`
- Centralized configuration management
- Reads API key from environment variable or Secrets file
- All scripts now use `get_api_key()` function

### 2. ✅ Created `.gitignore`
Protected files:
- `Secrets` file (contains your API key)
- `.env` files
- `*.db` files (your local cache)
- Python cache files (`__pycache__/`)
- IDE files (`.vscode/`, `.idea/`)

### 3. ✅ Updated All Scripts
All scripts now load the API key securely:
- ✅ `app.py`
- ✅ `example_usage.py`
- ✅ `get_yesterday_cached.py`
- ✅ `get_date.py`
- ✅ `cached_examples.py`
- ✅ `sync_year_data.py`
- ✅ `get_yesterday.py`

### 4. ✅ Created Documentation
- `README_GITHUB.md` - Main GitHub README
- `GITHUB_SETUP.md` - This file
- `APP_GUIDE.md` - Application guide

---

## 🚀 Push to GitHub

### Step 1: Verify No Secrets Will Be Committed

```bash
cd "/Users/juanortiz/Projects/web-apps/portal-base"

# Check what will be committed
git status

# Verify the Secrets file is ignored
git check-ignore Secrets
# Should output: Secrets

# Verify .db files are ignored  
git check-ignore base_cache.db
# Should output: base_cache.db
```

### Step 2: Initialize Git Repository (if not already done)

```bash
git init
git add .
git commit -m "Initial commit: Portal Base API Client"
```

### Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `portal-base-client`)
3. **DO NOT** initialize with README (you already have one)
4. Keep it public or private as you prefer

### Step 4: Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/portal-base-client.git

# Rename README for GitHub
mv README.md README_OLD.md
mv README_GITHUB.md README.md

# Commit the README change
git add README.md README_OLD.md
git commit -m "Update README for GitHub"

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 🔐 Setting Up for Other Users

When others clone your repository, they need to set up their API key:

### Option 1: Environment Variable (Recommended)

**macOS/Linux:**
```bash
export BASE_API_KEY="their_api_key_here"

# Add to ~/.zshrc or ~/.bashrc for persistence
echo 'export BASE_API_KEY="their_api_key_here"' >> ~/.zshrc
```

**Windows:**
```cmd
set BASE_API_KEY=their_api_key_here

# For persistence, use System Properties > Environment Variables
```

### Option 2: Secrets File

Create a `Secrets` file in the project root:
```
BASE_API_KEY:"their_api_key_here"
```

---

## 📋 Post-Push Checklist

After pushing to GitHub, verify:

1. ✅ Visit your GitHub repository
2. ✅ Check that `Secrets` file is NOT visible
3. ✅ Check that `base_cache.db` is NOT visible
4. ✅ Check that README displays correctly
5. ✅ Test cloning in a new directory
6. ✅ Verify app runs with environment variable

### Test Clone Command

```bash
# Clone to a test directory
cd /tmp
git clone https://github.com/YOUR_USERNAME/portal-base-client.git
cd portal-base-client

# Set API key
export BASE_API_KEY="your_api_key_here"

# Install dependencies
pip install -r requirements.txt

# Test the app
streamlit run app.py
```

---

## ⚠️ If You Accidentally Committed Secrets

If you accidentally committed your API key:

### 1. Remove from History

```bash
# Install git-filter-repo if needed
# macOS: brew install git-filter-repo

# Remove Secrets file from all history
git filter-repo --path Secrets --invert-paths

# Force push (WARNING: rewrites history)
git push origin --force --all
```

### 2. Rotate Your API Key

Contact Base.gov.pt to get a new API key, as the old one may be compromised.

### 3. Update Local Configuration

Update your `Secrets` file or environment variable with the new key.

---

## 📝 Maintaining the Repository

### Adding New Features

```bash
git checkout -b feature/new-feature
# Make your changes
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
# Create Pull Request on GitHub
```

### Updating Dependencies

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### Keeping Your Fork Updated

```bash
git fetch origin
git checkout main
git merge origin/main
```

---

## 🎉 You're All Set!

Your project is now secure and ready for GitHub. The API key is:
- ✅ NOT in the code
- ✅ NOT in Git history
- ✅ Protected by `.gitignore`
- ✅ Loaded from environment/Secrets file

Happy coding! 🚀

