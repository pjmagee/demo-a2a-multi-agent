import httpx
import json

print("=== Testing Backend ===")
try:
    client = httpx.Client(timeout=5.0)
    response = client.get("http://localhost:8100/api/agents")
    print(f"Backend Status: {response.status_code}")
    print(f"Response length: {len(response.text)} chars")
    print(f"CORS Headers:")
    for key, val in response.headers.items():
        if 'access-control' in key.lower() or 'origin' in key.lower():
            print(f"  {key}: {val}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"\nAgents count: {len(agents)}")
        for agent in agents[:3]:
            print(f"  - {agent.get('name')}")
except Exception as e:
    print(f"Backend Error: {e}")

print("\n=== Simulating Frontend Fetch ===")
try:
    # This is exactly what the browser does
    response = client.get(
        "http://localhost:8100/api/agents?token=test123",
        headers={
            "Origin": "http://localhost:3000",
            "Referer": "http://localhost:3000/"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"CORS access-control-allow-origin: {response.headers.get('access-control-allow-origin', 'NOT SET')}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"Agents returned: {len(agents)}")
    else:
        print(f"Error response: {response.text[:200]}")
except Exception as e:
    print(f"Fetch Error: {e}")
