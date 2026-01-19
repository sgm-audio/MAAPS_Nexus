#!/usr/bin/env python3
"""
Test Vertex AI Integration for MAAPS Nexus

This script verifies that Vertex AI is properly configured and can connect.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_vertex_ai_connection():
    """Test Vertex AI connection"""
    print("=" * 60)
    print("MAAPS Nexus - Vertex AI Connection Test")
    print("=" * 60)
    print()

    # Check environment variables
    print("1. Checking environment variables...")
    project_id = os.getenv("VERTEX_PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    model = os.getenv("VERTEX_MODEL", "claude-3-5-sonnet@20241022")

    if not project_id:
        print("❌ ERROR: VERTEX_PROJECT_ID not set")
        print()
        print("Please set up your environment:")
        print("  export VERTEX_PROJECT_ID=your-project-id")
        print("  export VERTEX_LOCATION=us-central1")
        print("  export VERTEX_MODEL=claude-3-5-sonnet@20241022")
        print()
        print("Or add to .env file:")
        print("  VERTEX_PROJECT_ID=your-project-id")
        print("  VERTEX_LOCATION=us-central1")
        print("  VERTEX_MODEL=claude-3-5-sonnet@20241022")
        return False

    print(f"✅ VERTEX_PROJECT_ID: {project_id}")
    print(f"✅ VERTEX_LOCATION: {location}")
    print(f"✅ VERTEX_MODEL: {model}")
    print()

    # Check authentication
    print("2. Checking authentication...")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds:
        print(f"✅ Using service account: {google_creds}")
    else:
        print("ℹ️  Using Application Default Credentials")
        print("   (Run: gcloud auth application-default login)")
    print()

    # Test import
    print("3. Testing package imports...")
    try:
        from utils.vertex_ai_integration import VertexAIClient
        print("✅ Successfully imported VertexAIClient")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print()
        print("Please install required packages:")
        print("  pip install 'anthropic[vertex]' google-cloud-aiplatform")
        return False
    print()

    # Initialize client
    print("4. Initializing Vertex AI client...")
    try:
        client = VertexAIClient(
            project_id=project_id,
            location=location,
            model=model
        )
        print(f"✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print()
        print("Common issues:")
        print("  - Make sure you've enabled Vertex AI API:")
        print("    gcloud services enable aiplatform.googleapis.com")
        print("  - Make sure you're authenticated:")
        print("    gcloud auth application-default login")
        print("  - Make sure your project ID is correct")
        return False
    print()

    # Test connection
    print("5. Testing API connection...")
    try:
        result = client.test_connection()

        if result["status"] == "success":
            print(f"✅ CONNECTION SUCCESSFUL!")
            print(f"   Model: {result['model']}")
            print(f"   Location: {result['location']}")
            print(f"   Response: {result['response']}")
            print()
            print("=" * 60)
            print("🎉 VERTEX AI IS READY TO USE!")
            print("=" * 60)
            return True
        else:
            print(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        print()
        print("If you see authentication errors:")
        print("  1. Run: gcloud auth application-default login")
        print("  2. Or set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON")
        print()
        print("If you see API not enabled:")
        print("  1. Run: gcloud services enable aiplatform.googleapis.com")
        print("  2. Wait a few minutes for the API to activate")
        return False


def test_llm_integration():
    """Test unified LLM integration layer"""
    print()
    print("=" * 60)
    print("Testing Unified LLM Integration Layer")
    print("=" * 60)
    print()

    try:
        from utils.llm_integration import create_llm_client

        # Test Vertex AI through unified interface
        print("Testing create_llm_client with Vertex AI provider...")
        client = create_llm_client(provider="vertex_ai")

        response = client.chat(
            messages=[{"role": "user", "content": "Say 'Hello from MAAPS Nexus' only."}],
            max_tokens=20
        )

        print(f"✅ Unified LLM client works!")
        print(f"   Response: {response}")
        print()
        return True

    except Exception as e:
        print(f"❌ Unified client test failed: {e}")
        return False


if __name__ == "__main__":
    print()

    # Run tests
    vertex_ok = test_vertex_ai_connection()

    if vertex_ok:
        llm_ok = test_llm_integration()

        if llm_ok:
            print()
            print("✅ ALL TESTS PASSED")
            print()
            print("Next steps:")
            print("  1. Use VertexAIClient directly for Vertex AI")
            print("  2. Use create_llm_client() for unified interface")
            print("  3. Integrate into your MAAPS agents")
            sys.exit(0)

    print()
    print("❌ SOME TESTS FAILED")
    print("   Please fix the issues above and try again")
    sys.exit(1)
