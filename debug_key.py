#!/usr/bin/env python3
"""
Debug API key loading to see what's happening.
"""

import os
from dotenv import load_dotenv

def debug_api_key():
    """Debug API key loading"""
    
    print("🔍 Debugging API key loading...")
    
    # Method 1: Using python-dotenv (like test script)
    load_dotenv()
    key1 = os.getenv('OPENAI_API_KEY')
    print(f"Method 1 (dotenv): {key1[:20] if key1 else 'None'}... (length: {len(key1) if key1 else 0})")
    
    # Method 2: Manual parsing (like document reviewer)
    key2 = None
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'OPENAI_API_KEY':
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        key2 = value
                        break
    
    print(f"Method 2 (manual): {key2[:20] if key2 else 'None'}... (length: {len(key2) if key2 else 0})")
    
    # Compare
    if key1 == key2:
        print("✅ Both methods return the same key")
    else:
        print("❌ Keys are different!")
        print(f"Difference: '{key1}' vs '{key2}'")
        if key1 and key2:
            print(f"Key1 repr: {repr(key1)}")
            print(f"Key2 repr: {repr(key2)}")

if __name__ == "__main__":
    debug_api_key()