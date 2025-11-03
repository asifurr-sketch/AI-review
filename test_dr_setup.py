#!/usr/bin/env python3
"""
Simple test of document reviewer API key and client initialization.
"""

import os
from openai import OpenAI

def test_document_reviewer_setup():
    """Test the same setup as document reviewer"""
    
    print("🔍 Testing document reviewer setup...")
    
    # Load API key exactly like document reviewer
    def _load_openai_api_key():
        """Load OpenAI API key from .env file or environment variable"""
        # First check .env file (more user-friendly for cross-platform)
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
                            return value
        
        # Fallback to environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        return None
    
    api_key = _load_openai_api_key()
    if not api_key:
        print("❌ No API key found")
        return
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created")
        
        # Test a simple call like the document reviewer would
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": "Test message"
                }
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_document_reviewer_setup()