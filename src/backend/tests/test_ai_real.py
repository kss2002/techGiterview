
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env dev manually
load_dotenv("src/backend/.env.dev")

# Add src/backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.ai_service import ai_service, AIProvider
from app.api.analysis import router
from app.core.config import settings

async def verify_ai_real():
    print("--- Real AI Service Verification ---")
    
    # Check loaded keys
    print(f"Upstage Key in Env: {bool(os.getenv('UPSTAGE_API_KEY'))}")
    print(f"Google Key in Env: {bool(os.getenv('GOOGLE_API_KEY'))}")
    
    # Force re-init to pick up env vars if needed
    # (In real app, settings are loaded at start, but here we might need to patch or reload)
    # ai_service._initialize_providers() called at import time might have missed env if not set before import.
    # But settings loads from .env.dev automatically if class Config matches.
    
    print("Available Providers:", ai_service.get_available_providers())
    
    provider_upstage = ai_service.available_providers.get(AIProvider.UPSTAGE_SOLAR)
    
    if provider_upstage:
        print("✅ Upstage Provider is AVAILABLE.")
        prompt = "Answer 'Yes' if you see this."
        try:
            print("Sending test generation request...")
            # We must pass the key explicitly or rely on settings. 
            # Settings might have cached empty if imported before load_dotenv in main process?
            # Let's check settings value
            print(f"Settings Upstage Key: {bool(settings.upstage_api_key)}")
            
            # If settings is empty, we might need to update it manually for this test context or assume main.py handles it better.
            # But let's try generating
            response = await ai_service.generate_analysis(prompt, provider=AIProvider.UPSTAGE_SOLAR)
            print("✅ Generation Result:", response)
        except Exception as e:
            print("❌ Generation Failed:", e)
    else:
        print("❌ Upstage Provider is MISSING. (Check config loading)")

if __name__ == "__main__":
    asyncio.run(verify_ai_real())
