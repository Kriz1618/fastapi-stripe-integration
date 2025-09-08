#!/usr/bin/env python3
"""
Script to run tests for FastAPI Stripe Integration
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle the result"""
    print(f"\n🧪 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner"""
    print("🚀 FastAPI Stripe Integration - Test Runner")
    print("=" * 60)

    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    # Check if we're in the right directory
    if not os.path.exists("app") or not os.path.exists("tests"):
        print("❌ Could not find app or tests directories")
        sys.exit(1)

    # Install test dependencies
    if not run_command("pip install -r tests/requirements-test.txt", "Installing test dependencies"):
        sys.exit(1)

    # Run different test suites
    test_commands = [
        ("pytest tests/test_auth_endpoints.py -v", "Running Authentication Tests"),
        ("pytest tests/test_stripe_endpoints.py -v", "Running Stripe Integration Tests"),
        ("pytest tests/test_notification_endpoints.py -v", "Running Notification Tests"),
        ("pytest tests/test_webhook_handlers.py -v", "Running Webhook Handler Tests"),
    ]

    # Run all tests
    print("\n" + "=" * 60)
    print("🎯 Running All Test Suites")
    print("=" * 60)

    failed_tests = []

    for command, description in test_commands:
        if not run_command(command, description):
            failed_tests.append(description)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    if failed_tests:
        print(f"❌ {len(failed_tests)} test suite(s) failed:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\n🔍 Run individual test files to see detailed error messages")
    else:
        print("✅ All test suites passed successfully!")

        # Run coverage report
        print("\n📈 Generating Coverage Report...")
        run_command("pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov",
                   "Coverage Analysis")
        print("📂 HTML coverage report generated in: htmlcov/index.html")

    print("\n" + "=" * 60)
    print("🔧 Useful Test Commands:")
    print("=" * 60)
    print("# Run all tests:")
    print("pytest")
    print()
    print("# Run specific test file:")
    print("pytest tests/test_notification_endpoints.py")
    print()
    print("# Run tests with coverage:")
    print("pytest --cov=app")
    print()
    print("# Run tests matching pattern:")
    print("pytest -k 'notification'")
    print()
    print("# Run tests with verbose output:")
    print("pytest -v")
    print("=" * 60)


if __name__ == "__main__":
    main()
