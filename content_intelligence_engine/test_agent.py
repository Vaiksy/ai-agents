#!/usr/bin/env python3
"""
Test Script for Content Intelligence Engine v5.1

Run this after applying fixes to verify everything works.
"""

import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)

def test_server_running():
    """Test if server is running."""
    print_header("1. Testing Server Status")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✓ Server is running")
        print(f"  Status Code: {response.status_code}")
        data = response.json()
        print(f"  Version: {data.get('version')}")
        print(f"  Note: {data.get('note')}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Server is NOT running!")
        print("  Start with: uvicorn api.app:app --reload --host 127.0.0.1 --port 8000")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_health():
    """Test health endpoint."""
    print_header("2. Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        print(f"\nAPI: {data.get('api')}")
        
        ollama = data.get('ollama', {})
        print(f"\nOllama Status:")
        print(f"  Running: {ollama.get('ollama_running')}")
        print(f"  Models: {ollama.get('models')}")
        print(f"  Embeddings: {ollama.get('embeddings_available')}")
        
        if ollama.get('ollama_running') and ollama.get('models', {}).get('qwen2.5-coder:7b'):
            print("\n✓ All systems ready!")
            return True
        else:
            print("\n⚠ Ollama or models not ready")
            if not ollama.get('ollama_running'):
                print("  Run: ollama serve")
            if not ollama.get('models', {}).get('qwen2.5-coder:7b'):
                print("  Run: ollama pull qwen2.5-coder:7b")
            return False
            
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_debug_imports():
    """Test debug imports endpoint."""
    print_header("3. Testing Module Imports")
    
    try:
        response = requests.get(f"{BASE_URL}/debug/test", timeout=10)
        data = response.json()
        
        if data.get('imports') == 'success':
            print("✓ All modules imported successfully")
            for module, status in data.get('modules', {}).items():
                print(f"  {module}: {status}")
            return True
        else:
            print("✗ Import failed")
            print(f"  Error: {data.get('error')}")
            print(f"\nTraceback:\n{data.get('traceback')}")
            return False
            
    except Exception as e:
        print(f"✗ Debug test failed: {e}")
        return False


def test_analyze_quick():
    """Test analyze endpoint with minimal query."""
    print_header("4. Testing Analyze Endpoint (Quick Test)")
    
    print("⚠ This may take 2-5 minutes...")
    print("  Starting analysis...\n")
    
    payload = {
        "niche": "AI productivity tools",
        "platform": "LinkedIn",
        "audience": "Tech founders",
        "goal": "Build awareness"
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            timeout=600  # 10 minute timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Elapsed Time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                result = data.get('data', {})
                
                print("\n✓ Analysis completed successfully!")
                print(f"\nResult Summary:")
                print(f"  Research samples: {result.get('meta', {}).get('research_count')}")
                print(f"  Pages with content: {result.get('meta', {}).get('pages_with_content')}")
                print(f"  Pages summarized: {result.get('meta', {}).get('pages_summarized')}")
                print(f"  Gaps found: {result.get('meta', {}).get('gaps_found')}")
                print(f"  Signal strength: {result.get('signal_strength', {}).get('confidence')}")
                print(f"  Pipeline time: {result.get('meta', {}).get('elapsed_seconds')}s")
                
                # Check strategy sections
                strategy = result.get('content_strategy', {})
                print(f"\nStrategy Sections Generated:")
                for key in ['positioning', 'pillars', 'hooks', 'scripts', 'ctas', 'calendar']:
                    has_it = "✓" if strategy.get(key) else "✗"
                    print(f"  {has_it} {key}")
                
                print(f"\n📄 Full result saved to test_result.json")
                with open('test_result.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                return True
            else:
                print(f"\n✗ Analysis failed: {data.get('error')}")
                return False
        else:
            print(f"\n✗ Request failed")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out (>10 minutes)")
        print("  The analysis is taking too long")
        return False
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("CONTENT INTELLIGENCE ENGINE - TEST SUITE v5.1")
    print("="*70)
    print("\nThis will test your fixed Content Intelligence Agent")
    print("\nPrerequisites:")
    print("  1. ollama serve (running in Terminal 1)")
    print("  2. uvicorn api.app:app --reload (running in Terminal 2)")
    print("  3. qwen2.5-coder:7b model installed")
    print("\nPress Enter to start tests...")
    input()
    
    results = {}
    
    # Test 1: Server
    results['Server Running'] = test_server_running()
    if not results['Server Running']:
        print("\n❌ Server not running. Cannot continue tests.")
        return 1
    
    time.sleep(1)
    
    # Test 2: Health
    results['Health Check'] = test_health()
    time.sleep(1)
    
    # Test 3: Imports
    results['Module Imports'] = test_debug_imports()
    time.sleep(1)
    
    # Test 4: Analyze (only if previous tests pass)
    if all([results['Server Running'], results['Health Check'], results['Module Imports']]):
        print("\n✓ All prerequisite tests passed")
        print("\nProceed with full analyze test? This will take 2-5 minutes.")
        print("Press Enter to continue or Ctrl+C to skip...")
        try:
            input()
            results['Analyze Endpoint'] = test_analyze_quick()
        except KeyboardInterrupt:
            print("\n⚠ Skipped analyze test")
            results['Analyze Endpoint'] = None
    else:
        print("\n⚠ Skipping analyze test due to prerequisite failures")
        results['Analyze Endpoint'] = None
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    for test_name, passed in results.items():
        if passed is None:
            symbol = "⊘"
            status = "SKIPPED"
        elif passed:
            symbol = "✓"
            status = "PASSED"
        else:
            symbol = "✗"
            status = "FAILED"
        print(f"{symbol} {test_name}: {status}")
    
    all_passed = all(v for v in results.values() if v is not None)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour Content Intelligence Agent is working correctly.")
        print("\nYou can now use the /analyze endpoint:")
        print(f"  POST {BASE_URL}/analyze")
        print("\nSee test_result.json for sample output.")
    else:
        print("\n⚠ SOME TESTS FAILED")
        print("\nCheck the error messages above and:")
        print("  1. Make sure ollama serve is running")
        print("  2. Make sure qwen2.5-coder:7b is installed")
        print("  3. Make sure all fixed files are in place")
        print("  4. Check server logs for detailed errors")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(1)
