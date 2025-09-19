#!/usr/bin/env python3
"""
Script to configure pre-commit hooks for automatic linting
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Configure pre-commit hooks"""
    project_root = Path(__file__).parent.parent

    print("🔧 Configuring pre-commit hooks...")
    print(f"📁 Project: {project_root}")

    try:
        # Install pre-commit if not installed
        print("\n1. Checking pre-commit installation...")
        result = subprocess.run(["pre-commit", "--version"], capture_output=True)
        if result.returncode != 0:
            print("❌ Pre-commit not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], check=True)
            print("✅ Pre-commit installed")
        else:
            print("✅ Pre-commit already installed")

        # Install hooks
        print("\n2. Installing hooks...")
        subprocess.run(["pre-commit", "install"], cwd=project_root, check=True)
        subprocess.run(["pre-commit", "install", "--hook-type", "pre-push"], cwd=project_root, check=True)
        print("✅ Hooks installed")

        # Run once to download dependencies
        print("\n3. Setting up dependencies...")
        result = subprocess.run(["pre-commit", "run", "--all-files"], cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Some files were modified by formatters")
            print("💡 This is normal the first time")
        else:
            print("✅ Everything configured correctly")

        print("\n🎉 Pre-commit configured successfully!")
        print("\nNow:")
        print("• Linters will run automatically on each commit")
        print("• Formatters will fix code automatically")
        print("• To run manually: pre-commit run --all-files")
        print("• To skip hooks: git commit --no-verify")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error configuring pre-commit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
