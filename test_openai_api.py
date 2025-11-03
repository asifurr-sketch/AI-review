#!/usr/bin/env python3
"""
Test script to verify OpenAI API key and check available models.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

def test_openai_api():
    """Test OpenAI API connection and list available models."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ Found OpenAI API key: {api_key[:10]}...")
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Test API connection by listing models
        print("\n🔍 Testing API connection...")
        models = client.models.list()
        
        print("✅ API connection successful!")
        print(f"📊 Found {len(models.data)} available models")
        
        # Look for GPT models
        gpt_models = [model.id for model in models.data if 'gpt' in model.id.lower()]
        o_models = [model.id for model in models.data if model.id.startswith('o')]
        
        print(f"\n🤖 Available GPT models ({len(gpt_models)}):")
        for model in sorted(gpt_models):
            print(f"  - {model}")
            
        print(f"\n🧠 Available O-series models ({len(o_models)}):")
        for model in sorted(o_models):
            print(f"  - {model}")
        
        # Test a simple chat completion
        print("\n💬 Testing chat completion with gpt-4o...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": "Hello! Just testing the API. Please respond with 'API test successful!'"}
                ],
                max_tokens=50
            )
            
            print("✅ Chat completion test successful!")
            print(f"Response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"❌ Chat completion test failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OpenAI API...")
    success = test_openai_api()
    
    if success:
        print("\n✅ All tests passed! OpenAI API is working correctly.")
    else:
        print("\n❌ API tests failed. Please check your API key and try again.")