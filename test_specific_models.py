#!/usr/bin/env python3
"""
Test specific OpenAI models to see which ones work with our API key.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

def test_specific_models():
    """Test specific models we want to use."""
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Models to test
    models_to_test = [
        "gpt-5",
        "gpt-5-pro", 
        "gpt-4o",
        "o3-deep-research",
        "o1",
        "gpt-4o-mini"
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Testing {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello from " + model + "!' and nothing else."}
                ],
                max_tokens=50
            )
            
            result = response.choices[0].message.content
            print(f"✅ {model}: {result}")
            
        except Exception as e:
            print(f"❌ {model}: {str(e)}")

if __name__ == "__main__":
    test_specific_models()