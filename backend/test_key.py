import os
import sys

# 1. Fix the Import Error
try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: 'python-dotenv' is not installed.")
    print("   Run: pip install python-dotenv")
    sys.exit(1)

# 2. Suppress the Deprecation Warning (It's just a warning, not an error)
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai

# Load the environment variables
load_dotenv()

def test_api_key():
    print("--- DIAGNOSTIC TEST ---")
    
    # Check if Key Exists
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY is missing from environment.")
        print(f"   Searching in: {os.getcwd()}")
        print("   Make sure your .env file is in the same folder you are running this command from.")
        return

    print(f"✅ API Key found: {api_key[:5]}...{api_key[-5:]}")

    # Check if Key Works
    try:
        genai.configure(api_key=api_key)
        print("   Connecting to Google servers...")
        
        # Simple test generation
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        
        print(f"✅ Connection Successful!")
        print(f"   Response from AI: {response.text}")
        
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        print("\nPossible fixes:")
        print("1. Your API key might be invalid.")
        print("2. 'gemini-1.5-flash' might not be enabled for your API key.")
        print("3. Try changing the model to 'gemini-pro' in your main code.")

if __name__ == "__main__":
    test_api_key()