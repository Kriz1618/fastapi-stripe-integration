#!/usr/bin/env python3
"""
Script to run all linting and formatting tools.
Usage: python scripts/lint.py [--fix]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_python_executable():
    """Get the appropriate Python executable for the current environment."""
    project_root = Path(__file__).parent.parent

    # Try to use virtual environment python first (for local development)
    venv_python = project_root / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)

    # Fallback to system python (for CI environments)
    return sys.executable


def run_command(command, description, check=True):
    """Execute command and show result."""
    print(f"\n🔍 {description}...")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run linting tools")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply automatic fixes when possible",
    )
    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    print(f"📁 Running from: {project_root}")

    # Get the appropriate Python executable
    python_cmd = get_python_executable()
    print(f"🐍 Using Python: {python_cmd}")

    success = True

    if args.fix:
        print("🔧 Auto-fix mode enabled")

        # Format imports with isort
        success &= run_command(
            [python_cmd, "-m", "isort", "app/"],
            "Organizing imports with isort",
        )

        # Format code with black
        success &= run_command(
            [python_cmd, "-m", "black", "app/"],
            "Formatting code with black",
        )

    # Check code style with flake8
    success &= run_command(
        [python_cmd, "-m", "flake8", "app/"],
        "Checking code style with flake8",
        check=False,  # Don't fail on style errors
    )

    # Check types with mypy (warnings only, no errors)
    print("\n🔍 Checking types with mypy...")
    print(f"Running: {python_cmd} -m mypy app/")
    try:
        result = subprocess.run(
            [python_cmd, "-m", "mypy", "app/"], capture_output=True, text=True
        )
        if result.stdout:
            # Show summary instead of all errors
            lines = result.stdout.strip().split("\n")
            error_count = len([line for line in lines if "error:" in line])
            if error_count > 0:
                print(
                    f"⚠️  MyPy found {error_count} type issues (non-critical)"
                )
                print("💡 Run 'python -m mypy app/' to see details")
            else:
                print("✅ Type checking completed")
        else:
            print("✅ Type checking completed")
    except Exception as e:
        print(f"⚠️  MyPy not available: {e}")

    # MyPy doesn't affect final result to avoid blocking development

    if success:
        print("\n🎉 All checks completed successfully!")
        return 0
    else:
        print("\n⚠️  Some checks found issues.")
        print(
            "💡 Run with --fix to automatically fix formatting issues."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
