import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "your_api_key_here":
    print("ERROR: No API key found in .env file!")
    print("Please add your OpenAI API key to the .env file")
    exit(1)

print(f"API Key found: {api_key[:20]}...{api_key[-4:]}")
print("Testing connection to OpenAI...")

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'API key works!' if you can read this."}],
        max_tokens=10
    )
    
    print(f"\nSUCCESS! OpenAI responded: {response.choices[0].message.content}")
    print("Your API key is valid and working!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    print("Your API key may be invalid or there's a connection issue.")
