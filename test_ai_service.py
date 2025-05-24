#!/usr/bin/env python3
"""
Test if the AI service (Ollama) is running and accessible.
"""
import requests
import json

# Test AI service
ai_url = "http://localhost:11434/api/generate"
test_prompt = "Say hello in 5 words or less."

print("Testing AI service (Ollama)...")
print(f"URL: {ai_url}")
print(f"Test prompt: {test_prompt}")
print("-" * 50)

try:
    # First, check if service is running
    response = requests.get("http://localhost:11434")
    print(f"✅ Service is reachable. Status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ AI service (Ollama) is NOT running!")
    print("\nTo fix this, you need to:")
    print("1. Install Ollama: https://ollama.ai/")
    print("2. Start Ollama service")
    print("3. Pull a model: ollama pull mistral")
    exit(1)

# Try to generate a response
try:
    payload = {
        "model": "mistral",  # or another model you have
        "prompt": test_prompt,
        "stream": False
    }
    
    print("\nSending test request...")
    response = requests.post(ai_url, json=payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ AI response received!")
        print(f"Response: {result.get('response', 'No response field')}")
    else:
        print(f"❌ Error: Status code {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error calling AI service: {e}")

# List available models
try:
    print("\n\nChecking available models...")
    response = requests.get("http://localhost:11434/api/tags")
    if response.status_code == 200:
        models = response.json().get('models', [])
        if models:
            print("Available models:")
            for model in models:
                print(f"  - {model['name']} (size: {model.get('size', 'unknown')})")
        else:
            print("❌ No models installed!")
            print("Install a model with: ollama pull mistral")
    else:
        print(f"❌ Could not list models: {response.status_code}")
except Exception as e:
    print(f"❌ Error listing models: {e}")
