#!/usr/bin/env python3
"""Development environment setup script for InferLine."""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, cwd: Path = None) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, cwd=cwd,
            capture_output=True, text=True
        )
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Set up development environment."""
    print("Setting up InferLine development environment...")
    
    project_root = Path(__file__).parent.parent
    
    # Install package in development mode
    if not run_command("pip install -e .", project_root):
        sys.exit(1)
    
    # Install development dependencies
    if not run_command("pip install -e '.[dev,docs]'", project_root):
        sys.exit(1)
    
    # Set up pre-commit hooks
    if not run_command("pre-commit install", project_root):
        print("Warning: pre-commit hooks not installed")
    
    print("\n✅ Development environment setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure")
    print("2. Run 'make docker-up' to start services")
    print("3. Run 'make test' to verify installation")

if __name__ == "__main__":
    main()