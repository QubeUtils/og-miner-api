import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.main import app

def generate_openapi():
    print("Generating OpenAPI schema...")
    openapi_schema = app.openapi()
    
    output_path = project_root / "openapi.json"
    
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
        
    print(f"OpenAPI schema saved to {output_path}")

if __name__ == "__main__":
    generate_openapi()
