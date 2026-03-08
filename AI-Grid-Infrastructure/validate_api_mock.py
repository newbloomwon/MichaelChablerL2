import requests

print("Testing API /grid/status (Normal)")
r = requests.get('http://127.0.0.1:8000/grid/status?texas_freq=60&maine_gas_mix=40&maine_price=50')
print(r.json())

print("\nTesting API /grid/status (Texas Reliability Mode)")
r = requests.get('http://127.0.0.1:8000/grid/status?texas_freq=59.9&maine_gas_mix=40&maine_price=50')
rj = r.json()
print(rj)

# Send throttle command from texas_eval
texas_eval = rj['texas']
command = {
    "state": "Texas",
    "reduction_percentage": texas_eval["reduction_percentage"],
    "reason": texas_eval["trigger_reason"]
}
print("\nSending throttle command to Mock Server...")
rt = requests.post('http://127.0.0.1:8001/throttle', json=command)
print(rt.json())
