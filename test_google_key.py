import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    print("Error: GOOGLE_API_KEY not found in environment.")
    exit(1)

try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    print("Sending test message to Gemini...")
    response = llm.invoke("Hello, simple test. Reply with 'Confirmed'.")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Verification Failed: {e}")
