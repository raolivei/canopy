#!/usr/bin/env python3
"""Test script for AI Assistant setup."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ollama_connection():
    """Test Ollama server connection."""
    print("🔍 Testing Ollama connection...")
    try:
        from ollama import Client
        client = Client(host="http://localhost:11434")
        
        # Test connection by listing models
        result = client.list()
        print(f"✅ Ollama connected! Available models:")
        for model in result.get('models', []):
            print(f"   - {model['name']}")
        return True
    except ImportError:
        print("❌ Ollama package not installed. Run: pip install ollama")
        return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False


def test_function_definitions():
    """Test function definitions are valid."""
    print("\n🔍 Testing function definitions...")
    try:
        from services.assistant_service import AssistantService
        
        funcs = AssistantService.FUNCTION_DEFINITIONS
        print(f"✅ Found {len(funcs)} function definitions:")
        for func in funcs:
            name = func['function']['name']
            desc = func['function']['description']
            print(f"   - {name}: {desc[:60]}...")
        return True
    except Exception as e:
        print(f"❌ Function definition test failed: {e}")
        return False


def test_imports():
    """Test all required imports."""
    print("\n🔍 Testing Python imports...")
    
    imports = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("ollama", "Ollama client"),
        ("openai", "OpenAI client (for OpenClaw)"),
    ]
    
    all_good = True
    for module, name in imports:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError:
            print(f"❌ {name} not installed. Run: pip install {module}")
            all_good = False
    
    return all_good


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Assistant Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test Ollama
    results.append(("Ollama Connection", test_ollama_connection()))
    
    # Test functions
    results.append(("Function Definitions", test_function_definitions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to test the assistant.")
        print("\nNext steps:")
        print("1. Start services: docker-compose up -d")
        print("2. Run migrations: docker-compose exec api alembic upgrade head")
        print("3. Open frontend: http://localhost:3001/assistant")
    else:
        print("\n⚠️  Some tests failed. Fix the issues above before proceeding.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
