
import asyncio
import os
import sys

# Add src/backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.ai_service import ai_service, AIProvider
from app.core.config import settings

async def test_ai():
    print("--- AI Service Connection Test ---")
    
    # Check Providers
    print("Available Providers:", ai_service.get_available_providers())
    
    # Check Keys
    print(f"Google Key present: {bool(settings.google_api_key)}")
    print(f"Upstage Key present: {bool(getattr(settings, 'upstage_api_key', None))}")
    
    # Test Generation
    prompt = "Hello, are you working? Please answer in one word."
    
    try:
        print(f"\nSending test request to {AIProvider.GEMINI_FLASH}...")
        response = await ai_service.generate_analysis(prompt, provider=AIProvider.GEMINI_FLASH)
        print("✅ Gemini Response:", response)
    except Exception as e:
        print("❌ Gemini Failed:", e)
        
    try:
        print(f"\nSending test request to {AIProvider.UPSTAGE_SOLAR}...")
        response = await ai_service.generate_analysis(prompt, provider=AIProvider.UPSTAGE_SOLAR)
        print("✅ Upstage Response:", response)
    except Exception as e:
        print("❌ Upstage Failed:", e)

if __name__ == "__main__":
    asyncio.run(test_ai())
