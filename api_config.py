import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

def configure_gemini():
    """Configure Gemini API with your key"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_actual_gemini_api_key_here":
        raise ValueError("❌ Please set your GEMINI_API_KEY in .env file")
    
    genai.configure(api_key=api_key)
    
    # Try gemini-2.5-flash, fallback to 1.5-flash
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        print("✅ Using gemini-2.5-flash")
        return model
    except Exception:
        print("⚠️ gemini-2.5-flash not available, using gemini-1.5-flash")
        return genai.GenerativeModel("gemini-1.5-flash")
