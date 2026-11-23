import urllib.request
import json

def verify():
    # 1. Test Root (SPA HTML)
    with urllib.request.urlopen('http://127.0.0.1:8000/') as r:
        html = r.read().decode('utf-8')
        assert 'MGH Freight Visibility Dashboard' in html
        print(f" Root HTML served successfully: Status {r.status}")

    # 2. Test Asset Serving
    with urllib.request.urlopen('http://127.0.0.1:8000/assets/index-DuUYxJHM.js') as r:
        js_len = len(r.read())
        print(f" JS Asset served successfully: {js_len} bytes")

    # 3. Test API Summary
    with urllib.request.urlopen('http://127.0.0.1:8000/api/summary') as r:
        data = json.loads(r.read().decode('utf-8'))
        print(f" API Summary: {data['total_shipments']} shipments, {data['on_time_percentage']}% on-time")

    # 4. Test API Ask
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/ask',
        data=json.dumps({'question': 'which carrier is delayed the most?'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as r:
        ask_data = json.loads(r.read().decode('utf-8'))
        print(f" API Ask engine: {ask_data['engine']}")
        print(f" Answer snippet: {ask_data['answer'][:90]}...")

    print(" ALL UNIFIED SINGLE-HOST ENDPOINTS ARE WORKING TOGETHER!")

if __name__ == '__main__':
    verify()
