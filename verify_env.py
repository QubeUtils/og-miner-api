
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import settings...")
    from app.core.config import settings
    print(f"SUCCESS: Settings loaded.")
    print(f"Project Name: {settings.PROJECT_NAME}")
    print(f"X_RAPIDAPI_PROXY_SECRET is set: {'Yes' if settings.X_RAPIDAPI_PROXY_SECRET else 'No'}")
    print(f"Redis URL: {settings.REDIS_URL}")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load settings. Reason: {e}")
    # Print detailed traceback
    import traceback
    traceback.print_exc()
    sys.exit(1)
