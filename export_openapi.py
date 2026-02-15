import json
import sys
import os

# Add the current directory to sys.path to make app module importable
sys.path.append(os.getcwd())

from app.main import app

def export_openapi():
    openapi_data = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(openapi_data, f, indent=2)
    print("OpenAPI specification exported to openapi.json")

if __name__ == "__main__":
    export_openapi()
