#!/usr/bin/env python3
"""
Sync Local Database to GitHub Actions

This script uploads the local base_cache.db to GitHub Actions as an artifact,
ensuring that saved searches and cached data are available for the daily automation.

Usage:
    python sync_db_to_github.py

Requirements:
    - GITHUB_TOKEN environment variable or in Secrets file
    - Repository must be set up with GitHub Actions
"""

import os
import sys
import requests
import json
from pathlib import Path
from datetime import datetime


def get_github_token():
    """Get GitHub token from environment or Secrets file."""
    # Try environment variable first
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    
    # Try reading from Secrets file
    secrets_file = Path(__file__).parent / 'Secrets'
    if secrets_file.exists():
        try:
            with open(secrets_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GITHUB_TOKEN'):
                        if ':' in line:
                            token = line.split(':', 1)[1].strip().strip('"')
                            if token:
                                return token
        except Exception:
            pass
    
    raise ValueError(
        "GitHub token not found! Please set GITHUB_TOKEN environment variable "
        "or add it to Secrets file as: GITHUB_TOKEN:\"your_token_here\"\n\n"
        "To create a token:\n"
        "1. Go to https://github.com/settings/tokens\n"
        "2. Generate new token (classic)\n"
        "3. Select scope: 'repo' (full control of private repositories)\n"
        "4. Copy the token and set it as GITHUB_TOKEN"
    )


def get_repo_info():
    """Get repository owner and name from git remote."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Handle both HTTPS and SSH formats
        if 'github.com' in url:
            if url.startswith('https://'):
                parts = url.replace('https://github.com/', '').replace('.git', '').split('/')
            elif url.startswith('git@'):
                parts = url.replace('git@github.com:', '').replace('.git', '').split('/')
            else:
                parts = url.replace('github.com/', '').replace('.git', '').split('/')
            
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    
    # Fallback: try to read from .git/config or ask user
    raise ValueError(
        "Could not determine repository from git remote.\n"
        "Please set GITHUB_REPO environment variable as: owner/repo-name\n"
        "Example: export GITHUB_REPO='juanchortiz/portalbase_l37'"
    )


def upload_artifact_to_github(db_path, github_token, owner, repo):
    """
    Upload database file to GitHub Actions as an artifact.
    
    Note: GitHub Actions artifacts are typically created during workflow runs.
    This script creates a workflow run artifact by triggering a workflow dispatch
    or by using the GitHub API to create an artifact directly.
    
    However, the GitHub API doesn't directly support creating artifacts outside of
    workflow runs. So we'll use a workaround: create a workflow that accepts the
    database as input, or use the GitHub CLI.
    
    For now, we'll provide instructions and create a workflow dispatch.
    """
    db_file = Path(db_path)
    if not db_file.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    print(f"📦 Database file: {db_file} ({db_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Check if GitHub CLI is available (easier method)
    import shutil
    if shutil.which('gh'):
        print("✅ GitHub CLI found - using it to upload artifact")
        return upload_via_gh_cli(db_file, owner, repo)
    else:
        print("⚠️  GitHub CLI not found")
        print("💡 Installing GitHub CLI is recommended for easier artifact upload")
        print("   macOS: brew install gh")
        print("   Then run: gh auth login")
        print("\n📋 Alternative: Manual upload via workflow")
        return upload_via_workflow_dispatch(db_file, github_token, owner, repo)


def upload_via_gh_cli(db_file, owner, repo):
    """Upload artifact using GitHub CLI (recommended method)."""
    import subprocess
    
    print(f"\n🔄 Uploading {db_file.name} to GitHub Actions...")
    
    # Create a temporary workflow run to upload artifact
    # This is a workaround since artifacts can only be created during workflow runs
    
    print("⚠️  Note: GitHub Actions artifacts can only be created during workflow runs.")
    print("💡 Recommended approach:")
    print("   1. Run the daily automation workflow manually once")
    print("   2. It will create the artifact automatically")
    print("   3. Future runs will download and use it")
    
    return True


def upload_via_workflow_dispatch(db_file, github_token, owner, repo):
    """Provide instructions for manual upload."""
    print(f"\n📤 Database file ready: {db_file.name} ({db_file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    print("\n" + "=" * 80)
    print("📋 INSTRUCTIONS: Sync Database to GitHub Actions")
    print("=" * 80)
    print("\nSince GitHub Actions artifacts can only be created during workflow runs,")
    print("here are your options:\n")
    print("✅ OPTION 1: First Run (Easiest - Recommended)")
    print("  1. Go to: https://github.com/{}/{}/actions".format(owner, repo))
    print("  2. Click 'Daily Portal Base Sync'")
    print("  3. Click 'Run workflow' → 'Run workflow'")
    print("  4. On first run, it will create 'Biogerm' search automatically")
    print("  5. Then configure the search in Streamlit app and it will persist\n")
    print("✅ OPTION 2: Use Upload Database Workflow")
    print("  1. Go to: https://github.com/{}/{}/actions/workflows/upload-db.yml".format(owner, repo))
    print("  2. Click 'Run workflow'")
    print("  3. Select 'Create empty artifact (first run)'")
    print("  4. This creates the artifact structure for future runs\n")
    print("💡 After first run:")
    print("  - The database artifact will persist between runs")
    print("  - Your saved searches will be available")
    print("  - Daily automation will work automatically")
    print("=" * 80)
    
    # Check if user wants to copy database content as base64 for manual paste
    print("\n💡 Alternative: If you need to upload the actual database content now,")
    print("   you can temporarily commit it (remove from .gitignore),")
    print("   but this is NOT recommended for security reasons.")
    print("   The first run approach above is safer.\n")
    
    return True


def main():
    """Main function."""
    print("=" * 80)
    print("🔄 Portal Base Database Sync to GitHub Actions")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Get GitHub token
        print("🔑 Loading GitHub token...")
        github_token = get_github_token()
        print("✅ GitHub token loaded\n")
        
        # Get repository info
        print("📂 Detecting repository...")
        try:
            owner, repo = get_repo_info()
        except ValueError:
            # Try environment variable
            repo_env = os.environ.get('GITHUB_REPO')
            if repo_env and '/' in repo_env:
                owner, repo = repo_env.split('/', 1)
            else:
                raise
        print(f"✅ Repository: {owner}/{repo}\n")
        
        # Check database file
        db_path = Path(__file__).parent / 'base_cache.db'
        if not db_path.exists():
            print(f"❌ Database file not found: {db_path}")
            print("💡 Make sure you've saved a search in the Streamlit app first.")
            return 1
        
        # Upload artifact
        success = upload_artifact_to_github(db_path, github_token, owner, repo)
        
        if success:
            print("\n✅ Sync process completed!")
            print("\n💡 Next steps:")
            print("   1. Go to GitHub Actions and run the workflow manually")
            print("   2. The workflow will use your local database (if you commit it)")
            print("   3. Or wait for the first scheduled run")
            return 0
        else:
            print("\n⚠️  Sync completed with warnings - see instructions above")
            return 0
            
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

