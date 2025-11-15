#!/usr/bin/env python3
"""
Simple Database Sync to GitHub

This script temporarily commits the database to sync it with GitHub Actions,
then removes it from the repository to keep it out of future commits.

Usage:
    python sync_db_simple.py

This will:
1. Temporarily remove base_cache.db from .gitignore
2. Commit and push the database
3. Restore .gitignore
4. The GitHub Actions workflow will download it on the next run
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Error running: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result


def main():
    """Main function."""
    print("=" * 80)
    print("🔄 Portal Base Database Sync to GitHub")
    print("=" * 80)
    print()
    
    repo_root = Path(__file__).parent
    db_file = repo_root / 'base_cache.db'
    gitignore_file = repo_root / '.gitignore'
    
    # Check if database exists
    if not db_file.exists():
        print("❌ Database file not found: base_cache.db")
        print("💡 Make sure you've saved a search in the Streamlit app first.")
        return 1
    
    db_size = db_file.stat().st_size / 1024 / 1024
    print(f"📦 Database file: {db_size:.2f} MB")
    
    if db_size > 100:
        print("⚠️  Warning: Database is large (>100MB). GitHub may reject it.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 1
    
    # Check if database is already tracked
    result = run_command("git ls-files base_cache.db", check=False)
    is_tracked = result.returncode == 0 and result.stdout.strip()
    
    if is_tracked:
        print("✅ Database is already tracked in git")
        print("🔄 Updating commit...")
    else:
        print("📝 Temporarily removing base_cache.db from .gitignore...")
        
        # Read .gitignore
        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()
        
        # Remove base_cache.db line
        lines = gitignore_content.split('\n')
        new_lines = [line for line in lines if 'base_cache.db' not in line]
        
        # Write back
        with open(gitignore_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ .gitignore updated")
    
    # Add database to git
    print("📤 Adding database to git...")
    run_command("git add base_cache.db")
    
    # Commit
    print("💾 Committing database...")
    run_command('git commit -m "Sync: Upload database for GitHub Actions (temporary)"')
    
    # Push
    print("🚀 Pushing to GitHub...")
    run_command("git push")
    
    # Restore .gitignore (if we modified it)
    if not is_tracked:
        print("🔄 Restoring .gitignore...")
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        
        # Remove from git tracking (but keep file)
        run_command("git rm --cached base_cache.db")
        run_command('git commit -m "Restore: Remove database from tracking"')
        run_command("git push")
        
        print("✅ .gitignore restored")
    
    print()
    print("=" * 80)
    print("✅ Database sync completed!")
    print("=" * 80)
    print()
    print("💡 Next steps:")
    print("   1. The database is now in the GitHub repository")
    print("   2. The next GitHub Actions run will download it")
    print("   3. Your saved searches will be available in the workflow")
    print("   4. The database will be removed from future commits")
    print()
    print("⚠️  Note: The database is temporarily in git history.")
    print("   If this is a concern, you can use git filter-branch to remove it later.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

