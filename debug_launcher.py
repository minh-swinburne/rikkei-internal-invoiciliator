#!/usr/bin/env python3
"""
Debug launcher to test portable path resolution and network connectivity.
"""

import sys
import os
import socket
import requests
from pathlib import Path
from urllib.parse import urlparse
import json

# Try to import OpenAI for comprehensive testing
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI package not available for testing")

def debug_paths():
    """Print debug information about paths and system state."""
    print("=== DEBUG PATH INFORMATION ===")
    print(f"sys.executable: {sys.executable}")
    print(f"__file__: {__file__}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Has _MEIPASS: {hasattr(sys, '_MEIPASS')}")
    
    if hasattr(sys, '_MEIPASS'):
        print(f"sys._MEIPASS: {sys._MEIPASS}")
    
    print("\n=== TESTING get_project_root() ===")
    try:
        # Add src to path
        current_dir = Path(__file__).parent
        src_dir = current_dir / "src"
        sys.path.insert(0, str(src_dir))
        
        from src.utils import get_project_root
        project_root = get_project_root()
        print(f"Project root: {project_root}")
        print(f"Project root exists: {project_root.exists()}")
        print(f"Project root is directory: {project_root.is_dir()}")
        
        # Test some expected paths
        test_paths = [
            project_root / "logs",
            project_root / "data",
            project_root / "data" / "input",
            project_root / "data" / "output"
        ]
        
        print("\n=== TESTING EXPECTED PATHS ===")
        for path in test_paths:
            print(f"{path}: exists={path.exists()}, is_dir={path.is_dir() if path.exists() else 'N/A'}")
            
    except Exception as e:
        print(f"Error testing get_project_root(): {e}")
        import traceback
        traceback.print_exc()

def test_basic_connectivity():
    """Test basic internet connectivity."""
    print("\n=== TESTING BASIC CONNECTIVITY ===")
    test_urls = [
        "https://www.google.com",
        "https://www.cloudflare.com", 
        "https://httpbin.org/get"
    ]
    
    for url in test_urls:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: {url} (Status: {response.status_code})")
                return True
            else:
                print(f"  ⚠️ UNEXPECTED: {url} (Status: {response.status_code})")
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ CONNECTION ERROR: {url} - {e}")
        except requests.exceptions.Timeout as e:
            print(f"  ❌ TIMEOUT: {url} - {e}")
        except Exception as e:
            print(f"  ❌ ERROR: {url} - {e}")
    
    print("❌ No internet connectivity detected")
    return False

def test_dns_resolution():
    """Test DNS resolution for key domains."""
    print("\n=== TESTING DNS RESOLUTION ===")
    test_domains = [
        "openrouter.ai",
        "api.openai.com",
        "google.com",
        "cloudflare.com"
    ]
    
    for domain in test_domains:
        try:
            ip_address = socket.gethostbyname(domain)
            print(f"  ✅ DNS OK: {domain} -> {ip_address}")
        except socket.gaierror as e:
            print(f"  ❌ DNS FAILED: {domain} - {e}")
        except Exception as e:
            print(f"  ❌ ERROR: {domain} - {e}")

def test_port_accessibility():
    """Test if HTTPS port (443) is accessible."""
    print("\n=== TESTING PORT ACCESSIBILITY ===")
    test_hosts = [
        ("openrouter.ai", 443),
        ("api.openai.com", 443),
        ("google.com", 443),
        ("httpbin.org", 443)
    ]
    
    for hostname, port in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                print(f"  ✅ PORT OK: {hostname}:{port}")
            else:
                print(f"  ❌ PORT BLOCKED: {hostname}:{port} (Error: {result})")
        except Exception as e:
            print(f"  ❌ ERROR: {hostname}:{port} - {e}")

def test_openai_client():
    """Test OpenAI client connectivity (matches actual implementation)."""
    print("\n=== TESTING OPENAI CLIENT ===")
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI package not available - skipping client tests")
        return
    
    try:
        # Get settings
        from src.settings import settings
        api_key = settings.llm_api_key
        base_url = settings.llm_base_url
        model = settings.llm_model
        
        print(f"Base URL: {base_url}")
        print(f"Model: {model}")
        print(f"API Key present: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"API Key format: {api_key[:10]}... (length: {len(api_key)})")
        
        if not api_key:
            print("❌ No API key configured - skipping client tests")
            return
        
        # Initialize OpenAI client (same as in actual implementation)
        print("Initializing OpenAI client...")
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,
            max_retries=2
        )
        print("  ✅ OpenAI client initialized successfully")
        
        # Test 1: Simple chat completion (like GUI test)
        print("Testing simple chat completion...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Respond with exactly one word: 'success'"}
                ],
                temperature=0.0,
                max_tokens=10,
                timeout=30.0
            )
            
            content = response.choices[0].message.content.strip().lower()
            print(f"  ✅ Chat completion successful - Response: '{content}'")
            
            if "success" in content:
                print("  ✅ Model responded correctly")
            else:
                print(f"  ⚠️ Unexpected response, but API is working")
            
        except Exception as e:
            print(f"  ❌ Chat completion failed: {type(e).__name__}: {e}")
            
            # More specific error handling
            if "401" in str(e) or "Unauthorized" in str(e):
                print("  🔑 Authentication error - Check your API key")
            elif "Connection" in str(e) or "connection" in str(e).lower():
                print("  🌐 Network connection error")
            elif "timeout" in str(e).lower():
                print("  ⏰ Request timed out")
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                print("  📈 Rate limit exceeded")
            return
        
        # Test 2: Structured output (if supported)
        print("Testing structured output support...")
        try:
            test_schema = {
                "type": "json_schema",
                "json_schema": {
                    "name": "test_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["status", "message"],
                        "additionalProperties": False
                    }
                }
            }
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Return a JSON object with status='ok' and message='structured output working'."},
                    {"role": "user", "content": "Please return the test JSON."}
                ],
                response_format=test_schema,
                temperature=0.0,
                max_tokens=50
            )
            
            content = response.choices[0].message.content
            try:
                parsed = json.loads(content)
                print(f"  ✅ Structured output successful - {parsed}")
            except json.JSONDecodeError:
                print(f"  ⚠️ Structured output returned non-JSON: {content}")
            
        except Exception as e:
            print(f"  ⚠️ Structured output test failed: {type(e).__name__}: {e}")
            print("  📝 This is normal for some models - fallback mode will be used")
        
        # Test 3: Test with actual invoice-like prompt (abbreviated)
        print("Testing invoice extraction prompt...")
        try:
            test_text = "INVOICE\nInvoice #: INV-001\nPO #: PO-001\nItem: Test Widget\nQty: 1\nPrice: $10.00"
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Extract invoice data and return as JSON with invoice_number and po_number fields."},
                    {"role": "user", "content": test_text}
                ],
                temperature=0.0,
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            print(f"  ✅ Invoice extraction test successful - Response length: {len(content)} chars")
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content.strip().replace("```json", "").replace("```", ""))
                if "invoice_number" in str(parsed).lower() or "inv-001" in str(parsed):
                    print("  ✅ Invoice data extraction working correctly")
                else:
                    print("  ⚠️ Response format unexpected but API is working")
            except:
                print("  ⚠️ Response not JSON but API is working")
            
        except Exception as e:
            print(f"  ❌ Invoice extraction test failed: {type(e).__name__}: {e}")
        
        print("✅ OpenAI client testing completed successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {type(e).__name__}: {e}")
        
        # Provide specific guidance based on error
        if "settings" in str(e).lower():
            print("  🔧 Settings loading issue - check if .env file exists")
        elif "import" in str(e).lower():
            print("  📦 Package import issue - check if OpenAI package is installed")
        else:
            print("  🔍 Check the detailed error above for more information")

def check_proxy_settings():
    """Check current proxy configuration."""
    print("\n=== CHECKING PROXY SETTINGS ===")
    
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'NO_PROXY', 'no_proxy'
    ]
    
    found_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"  {var}: {value}")
            found_proxy = True
    
    if not found_proxy:
        print("  No proxy environment variables found")
    
    # Check if requests is using system proxy
    try:
        print("\nTesting proxy detection...")
        response = requests.get('https://httpbin.org/ip', timeout=10)
        if response.status_code == 200:
            ip_info = response.json()
            print(f"  Your external IP: {ip_info.get('origin', 'unknown')}")
    except Exception as e:
        print(f"  Could not determine external IP: {e}")

def test_network_diagnostics():
    """Run comprehensive network diagnostics."""
    print("\n" + "="*60)
    print("🔍 COMPREHENSIVE NETWORK DIAGNOSTICS")
    print("="*60)
    
    # Test basic connectivity first
    has_internet = test_basic_connectivity()
    
    if has_internet:
        test_dns_resolution()
        test_port_accessibility()
        check_proxy_settings()
        test_openai_client()  # Updated function name
    else:
        print("\n⚠️ Skipping advanced tests due to no internet connectivity")
        check_proxy_settings()
    
    print("\n" + "="*60)
    print("🏁 NETWORK DIAGNOSTICS COMPLETE")
    print("="*60)

    print("\n=== TESTING SETTINGS IMPORT ===")
    try:
        from src.settings import settings
        print(f"Settings loaded successfully!")
        print(f"Input dir: {settings.input_dir}")
        print(f"Output dir: {settings.output_dir}")
    except Exception as e:
        print(f"Error loading settings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 INVOICE RECONCILIATOR DEBUG TOOL")
    print("="*60)
    print("This tool will help diagnose network and configuration issues.")
    print("Please share the complete output with the development team.")
    print("="*60)
    
    try:
        debug_paths()
        test_network_diagnostics()
        
        print("\n✅ All diagnostic tests completed!")
        print("📧 Please copy the entire output above and share it with the team.")
        
    except Exception as e:
        print(f"\n❌ Critical error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\nPress Enter to exit...")
