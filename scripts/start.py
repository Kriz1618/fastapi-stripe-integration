#!/usr/bin/env python3
"""
Simple script to run the FastAPI application locally
"""

import uvicorn
import sys
import os

if __name__ == "__main__":
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    # Add project root to Python path
    sys.path.insert(0, project_root)

    print("🚀 Starting Stripe Integration POC...")
    print("📚 Documentation available at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("👤 Users: http://localhost:8000/api/auth/")
    print("💳 Stripe: http://localhost:8000/api/stripe/")
    print("\n💡 To stop the application press Ctrl+C\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
