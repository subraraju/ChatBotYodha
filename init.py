#!/usr/bin/env python3
"""
Initialization script for first-time setup
"""
import os
import sys
from pathlib import Path


def create_init_files():
    """Create __init__.py files for proper package structure"""
    project_root = Path(__file__).parent

    init_dirs = ["app", "app/api", "app/models", "app/services", "app/chatbot"]

    for dir_path in init_dirs:
        init_file = project_root / dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"Created {init_file}")


def check_python_version():
    """Check if Python version is 3.12+"""
    if sys.version_info < (3, 12):
        print(f"❌ Python 3.12+ required. Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def main():
    """Main initialization"""
    print("🔧 Initializing Agentic Chatbot project...")

    if not check_python_version():
        sys.exit(1)

    create_init_files()

    print("✅ Initialization complete!")
    print("Next steps:")
    print("1. Configure your .env file with database and API credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Set up your PostgreSQL database with the SQL scripts")
    print("4. Run: python startup.py")


if __name__ == "__main__":
    main()
