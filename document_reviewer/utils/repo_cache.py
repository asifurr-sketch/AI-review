"""
Repository Cache Manager - Handles cloning and caching GitHub repositories
"""

import os
import subprocess
import re
import shutil
from typing import Optional, Tuple


class RepositoryCache:
    """Manages a cache of cloned GitHub repositories in project root/clones"""
    
    def __init__(self, quiet_mode: bool = False):
        self.quiet_mode = quiet_mode
        # Use project root clones folder instead of /tmp
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = os.path.join(project_root, "clones")
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_repo_name(self, url: str) -> str:
        """Extract the repository name from GitHub URL"""
        # Normalize URL
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract repo name from URL (e.g., https://github.com/owner/repo -> repo)
        match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', url, re.IGNORECASE)
        if match:
            return match.group(2)  # Return just the repo name
        
        # Fallback: use last part of URL
        return url.split('/')[-1]
    
    def _convert_to_ssh_url(self, https_url: str) -> str:
        """Convert HTTPS GitHub URL to SSH format"""
        if https_url.startswith('https://github.com/'):
            repo_path = https_url.replace('https://github.com/', '')
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            ssh_url = f"git@github.com:{repo_path}.git"
            return ssh_url
        return https_url
    
    def get_or_clone_repository(self, url: str) -> Optional[str]:
        """
        Get cached repository or clone it if not cached.
        Returns the path to the repository directory, or None if cloning fails.
        """
        # Generate cache path using actual repo name
        repo_name = self._get_repo_name(url)
        repo_dir = os.path.join(self.cache_dir, repo_name)
        
        # If directory already exists, delete it first (fresh clone)
        if os.path.exists(repo_dir):
            if not self.quiet_mode:
                print(f"🗑️  Removing existing repository: {repo_dir}")
            try:
                shutil.rmtree(repo_dir)
            except Exception as e:
                if not self.quiet_mode:
                    print(f"⚠️  Failed to remove existing directory: {e}")
                return None
        
        # Clone the repository
        if not self.quiet_mode:
            print(f"📦 Cloning repository to: {repo_dir}")
        
        return self._clone_repository(url, repo_dir)
    
    def _clone_repository(self, url: str, repo_dir: str) -> Optional[str]:
        """Clone GitHub repository to the specified directory"""
        try:
            # Convert HTTPS URL to SSH format
            ssh_url = self._convert_to_ssh_url(url)
            
            # Ensure directory doesn't exist
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir)
            
            # Try SSH first
            if not self.quiet_mode:
                print(f"🔑 Attempting to clone using SSH: {ssh_url}")
            
            result = subprocess.run([
                'git', 'clone', '--depth=1', ssh_url, repo_dir
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                if not self.quiet_mode:
                    print(f"✅ Successfully cloned via SSH to {repo_dir}")
                return repo_dir
            
            # Fallback to HTTPS
            if not self.quiet_mode:
                print(f"⚠️  SSH clone failed, trying HTTPS fallback...")
                print(f"   SSH Error: {result.stderr}")
            
            # Clean up failed attempt
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir)
            
            if not self.quiet_mode:
                print(f"🌐 Attempting to clone using HTTPS: {url}")
            
            https_result = subprocess.run([
                'git', 'clone', '--depth=1', url, repo_dir
            ], capture_output=True, text=True, timeout=120)
            
            if https_result.returncode == 0:
                if not self.quiet_mode:
                    print(f"✅ Successfully cloned via HTTPS to {repo_dir}")
                return repo_dir
            else:
                if not self.quiet_mode:
                    print(f"❌ Both SSH and HTTPS clone failed")
                    print(f"   SSH Error: {result.stderr}")
                    print(f"   HTTPS Error: {https_result.stderr}")
                    print(f"   ")
                    print(f"   💡 SSH Setup Help:")
                    print(f"   1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'")
                    print(f"   2. Add to SSH agent: ssh-add ~/.ssh/id_ed25519")
                    print(f"   3. Add public key to GitHub: cat ~/.ssh/id_ed25519.pub")
                    print(f"   4. Test SSH access: ssh -T git@github.com")
                return None
        
        except subprocess.TimeoutExpired:
            if not self.quiet_mode:
                print("❌ Git clone timed out after 120 seconds")
            return None
        except Exception as e:
            if not self.quiet_mode:
                print(f"❌ Git clone exception: {e}")
            return None
    
    def clear_cache(self):
        """Clear the entire repository cache"""
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            self._ensure_cache_dir()
            if not self.quiet_mode:
                print(f"🗑️  Repository cache cleared: {self.cache_dir}")
