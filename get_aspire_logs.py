import httpx
import json
import sys

def get_resources():
    client = httpx.Client(follow_redirects=True, timeout=10.0, verify=False)
    response = client.get("http://localhost:15197/api/resources")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response length: {len(response.text)}")
    print(f"First 200 chars: {response.text[:200]}")
    if response.status_code == 200:
        data = response.json()
        print("\nResources:")
        for r in data.get("resources", []):
            print(f"  - {r['name']} ({r['resourceType']})")
        return data.get("resources", [])
    return []

def get_console_logs(resource_name):
    print(f"\n{'='*60}")
    print(f"CONSOLE LOGS FOR: {resource_name}")
    print('='*60)
    client = httpx.Client(follow_redirects=True, timeout=10.0, verify=False)
    response = client.get(f"http://localhost:15197/api/logs/{resource_name}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        logs = response.json()
        log_lines = logs.get("logs", [])
        print(f"Found {len(log_lines)} log entries")
        # Show last 20 log entries
        for log in log_lines[-20:]:
            print(log)
    else:
        print(f"Error: {response.text[:200]}")

if __name__ == "__main__":
    resources = get_resources()
    
    # Get logs for backend and frontend
    for resource in resources:
        if resource['name'] in ['backend', 'frontend']:
            get_console_logs(resource['name'])
