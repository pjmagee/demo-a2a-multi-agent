"""Debug script to test registry connection."""
import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env file from the same directory as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


async def test_registry():
    """Test connection to A2A Registry."""
    registry_url = os.getenv("A2A_REGISTRY_URL", "http://127.0.0.1:8090")
    
    print(f"Registry URL from env: {registry_url!r}")
    print(f"All env vars with 'REGISTRY': {[k for k in os.environ if 'REGISTRY' in k]}")
    
    endpoint = f"{registry_url}/agents"
    
    print(f"\nTrying to connect to: {endpoint}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            print("Making GET request...")
            response = await client.get(endpoint)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            data = response.json()
            print(f"Response data: {data}")
            print(f"Number of agents: {len(data.get('agents', []))}")
            
            for agent in data.get("agents", []):
                print(f"  - {agent.get('name')} @ {agent.get('address')}")
                
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_registry())
