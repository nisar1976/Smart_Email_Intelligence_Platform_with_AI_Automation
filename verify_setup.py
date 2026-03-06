#!/usr/bin/env python3
"""Verification script for Email Intelligence Agent setup."""

import sys
import os
from pathlib import Path
import importlib.util

def check_python_version():
    """Check Python version."""
    print("Checking Python version...", end=" ")
    if sys.version_info >= (3, 9):
        print(f"✓ ({sys.version_info.major}.{sys.version_info.minor})")
        return True
    else:
        print(f"✗ (require 3.9+, have {sys.version_info.major}.{sys.version_info.minor})")
        return False

def check_venv():
    """Check if running in virtual environment."""
    print("Checking virtual environment...", end=" ")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓")
        return True
    else:
        print("⚠ (not in venv, recommended)")
        return True

def check_dependencies():
    """Check required dependencies."""
    print("\nChecking dependencies:")

    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'openai': 'OpenAI',
        'langchain': 'LangChain',
        'faiss': 'FAISS',
        'sentence_transformers': 'Sentence Transformers',
        'yaml': 'PyYAML',
        'pypdf': 'PyPDF',
        'requests': 'Requests',
    }

    all_ok = True
    for module, name in required.items():
        status = "✓" if importlib.util.find_spec(module) else "✗"
        symbol = "✓" if status == "✓" else "✗"
        all_ok = all_ok and (status == "✓")
        print(f"  {symbol} {name} ({module})")

    return all_ok

def check_files():
    """Check if all required files exist."""
    print("\nChecking project structure:")

    required_files = {
        'src/api/app.py': 'FastAPI app',
        'src/rag/loader.py': 'RAG loader',
        'src/rag/indexer.py': 'FAISS indexer',
        'src/rag/retriever.py': 'RAG retriever',
        'src/integrations/gmail_sender.py': 'Gmail sender',
        'frontend/package.json': 'Frontend config',
        'frontend/src/App.jsx': 'React App',
        'run.py': 'Launcher script',
        '.env.example': 'Environment template',
    }

    all_ok = True
    for file, description in required_files.items():
        path = Path(file)
        status = "✓" if path.exists() else "✗"
        symbol = "✓" if status == "✓" else "✗"
        all_ok = all_ok and (status == "✓")
        print(f"  {symbol} {file:40} ({description})")

    return all_ok

def check_env():
    """Check .env file."""
    print("\nChecking .env file:")

    env_path = Path('.env')
    if env_path.exists():
        print(f"  ✓ .env file exists")

        env_content = env_path.read_text()
        required_keys = [
            'OPENAI_API_KEY',
            'GMAIL_EMAIL',
            'GMAIL_APP_PASSWORD',
        ]

        configured = []
        missing = []

        for key in required_keys:
            if f'{key}=' in env_content:
                value = next((line.split('=')[1].strip() for line in env_content.split('\n')
                            if line.startswith(key + '=')), '')
                if value and value != '':
                    configured.append(key)
                else:
                    missing.append(key)
            else:
                missing.append(key)

        for key in configured:
            print(f"  ✓ {key} configured")

        for key in missing:
            print(f"  ⚠ {key} not configured")

        return len(configured) >= 1  # At least OpenAI key
    else:
        print(f"  ✗ .env file not found")
        print(f"  → Copy .env.example to .env and fill in your API keys")
        return False

def check_directories():
    """Check required directories."""
    print("\nChecking directories:")

    dirs = {
        'frontend': 'React frontend',
        'src': 'Python source',
        'src/api': 'API routes',
        'src/rag': 'RAG pipeline',
        'generated': 'Generated campaigns',
        'rag_index': 'FAISS index',
    }

    all_ok = True
    for dir_name, description in dirs.items():
        path = Path(dir_name)
        exists = path.exists()
        status = "✓" if exists else "○"
        symbol = "✓" if exists else "○"
        all_ok = all_ok and exists
        print(f"  {symbol} {dir_name:20} ({description})")

    return all_ok

def main():
    """Run all checks."""
    print("=" * 60)
    print("OHM Email Intelligence Agent - Setup Verification")
    print("=" * 60)
    print()

    results = {
        "Python Version": check_python_version(),
        "Virtual Environment": check_venv(),
        "Dependencies": check_dependencies(),
        "Project Files": check_files(),
        "Environment (.env)": check_env(),
        "Directories": check_directories(),
    }

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for check_name, passed in results.items():
        symbol = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        print(f"{symbol} {check_name:30} {status}")
        all_passed = all_passed and passed

    print()

    if all_passed:
        print("✓ All checks passed! Ready to start.")
        print()
        print("Next steps:")
        print("  1. Run: python run.py")
        print("  2. Browser opens to http://localhost:5173")
        print("  3. Go to Settings page and configure API keys")
        print("  4. Click 'Test Connections' to verify")
        print("  5. Use Generate page to create campaigns")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  • Missing dependencies: uv pip install -r requirements.txt")
        print("  • Missing .env: cp .env.example .env (then edit)")
        print("  • Missing frontend: Frontend auto-installs on first run")
        return 1

if __name__ == "__main__":
    sys.exit(main())
