import http.server
import socketserver
import json
import urllib.parse
import requests
from datetime import datetime, timedelta

# ===== CONFIG =====
API_KEY = "5a716a0761e23ac90c6a9cfc"  # Your key
PORT = 8000

# Global cache
rates_cache = {}
last_update = None

def fetch_rates():
    global rates_cache, last_update
    now = datetime.utcnow()
    if last_update is None or (now - last_update) > timedelta(hours=24):
        fetched = False
        # Try v6 (keyed) first
        try:
            print("📡 Trying v6 API (with key)...")
            url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
            res = requests.get(url, timeout=10)
            data = res.json()
            if data.get("result") == "success":
                rates_cache = data["rates"]
                fetched = True
                print("✅ v6 success. Currencies:", list(rates_cache.keys())[:5], "...")
        except Exception as e:
            print("⚠️ v6 failed:", e)

        # Fallback to v4 public (no key, but reliable for major currencies)
        if not fetched:
            try:
                print("🔁 Fallback to public API (v4)...")
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                res = requests.get(url, timeout=10)
                data = res.json()
                rates_cache = data["rates"]
                fetched = True
                print("✅ Public API success. Sample:", {k: rates_cache[k] for k in ["USD", "INR", "JPY", "EUR"] if k in rates_cache})
            except Exception as e:
                print("❌ Public API failed:", e)

        # Final fallback: hardcoded minimal rates (USD base)
        if not fetched:
            print("🛡️ Using minimal fallback rates...")
            rates_cache = {
                "USD": 1.0,
                "INR": 83.50,
                "JPY": 151.20,
                "EUR": 0.93,
                "GBP": 0.79,
                "CAD": 1.37,
                "AUD": 1.53
            }

        last_update = now
        print(f"✨ Rates ready ({len(rates_cache)} currencies). Next update: {last_update + timedelta(hours=24)}")

# Fetch on startup
fetch_rates()

# ===== HTML =====
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Currency Converter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 500px; margin: 30px auto; padding: 20px; background: #fafcff; }
        h2 { text-align: center; color: #0d4a3d; margin-bottom: 25px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ccd5dc; border-radius: 8px; font-size: 16px; }
        button { background: #0d4a3d; color: white; border: none; padding: 14px; width: 100%; font-size: 18px; border-radius: 8px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0a382e; }
        #result { margin-top: 24px; padding: 16px; background: #e6f7f4; border-radius: 8px; border-left: 4px solid #0d4a3d; font-weight: bold; }
        .debug { font-size: 0.8em; color: #64748b; text-align: center; margin-top: 20px; }
    </style>
</head>
<body>
    <h2>💱 Bharath Currency Converter</h2>
    <input type="number" id="amount" placeholder="Amount" value="1000" min="0.01" step="any">
    <select id="from">
        <option value="USD">US Dollar (USD)</option>
        <option value="INR" selected>Indian Rupee (INR)</option>
        <option value="JPY">Japanese Yen (JPY)</option>
        <option value="EUR">Euro (EUR)</option>
        <option value="GBP">British Pound (GBP)</option>
        <option value="CAD">Canadian Dollar (CAD)</option>
    </select>
    <select id="to">
        <option value="USD">US Dollar (USD)</option>
        <option value="INR">Indian Rupee (INR)</option>
        <option value="JPY" selected>Japanese Yen (JPY)</option>
        <option value="EUR">Euro (EUR)</option>
        <option value="GBP">British Pound (GBP)</option>
        <option value="CAD">Canadian Dollar (CAD)</option>
    </select>
    <button onclick="convert()">🔄 Convert</button>
    <div id="result">Result here</div>
    <div class="debug">Rates auto-refresh every 24h</div>

    <script>
        function convert() {
            const amt = parseFloat(document.getElementById('amount').value);
            const from = document.getElementById('from').value;
            const to = document.getElementById('to').value;
            if (!amt || amt <= 0) {
                document.getElementById('result').innerText = '⚠️ Enter amount > 0';
                return;
            }
            fetch(`/convert?amount=${amt}&from=${from}&to=${to}`)
                .then(r => r.json())
                .then(d => {
                    const resDiv = document.getElementById('result');
                    if (d.error) {
                        resDiv.innerHTML = `❌ <b>Error:</b> ${d.error}`;
                    } else {
                        resDiv.innerHTML = `
                            <span style="color:#0d4a3d">${amt.toLocaleString()} ${from}</span>
                            &nbsp;=&nbsp;
                            <span style="color:#006644">${d.result.toLocaleString(undefined, {maximumFractionDigits: 2})} ${to}</span>
                            <br><small>1 ${from} = ${d.rate.toFixed(4)} ${to}</small>
                        `;
                    }
                })
                .catch(e => {
                    document.getElementById('result').innerText = '⚠️ Network error: ' + e.message;
                });
        }
        window.onload = convert;
        document.getElementById('amount').addEventListener('keyup', e => {
            if (e.key === 'Enter') convert();
        });
    </script>
</body>
</html>
'''

# ===== SERVER =====
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/convert?'):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                amount = float(query.get('amount', [1])[0])
                from_curr = query.get('from', ['USD'])[0].upper()
                to_curr = query.get('to', ['INR'])[0].upper()

                # Log debug info
                print(f"\n🔍 Request: {amount} {from_curr} → {to_curr}")
                print(f"📊 Available currencies (first 10): {list(rates_cache.keys())[:10]}")

                usd_rate = rates_cache.get(from_curr)
                to_rate = rates_cache.get(to_curr)
                
                if usd_rate is None:
                    raise ValueError(f"Unsupported 'from' currency: {from_curr}. Supported: {', '.join(sorted(rates_cache.keys()))[:100]}...")
                if to_rate is None:
                    raise ValueError(f"Unsupported 'to' currency: {to_curr}. Supported: {', '.join(sorted(rates_cache.keys()))[:100]}...")

                result = (amount / usd_rate) * to_rate
                rate = to_rate / usd_rate

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "result": result,
                    "rate": rate,
                    "from": from_curr,
                    "to": to_curr
                }).encode())
            except Exception as e:
                print("❗ Error:", e)
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print("="*60)
    print("🚀 Bharath Currency Converter")
    print("🔗 http://localhost:8000")
    print("🔄 Rates auto-update daily (v6 → v4 → fallback)")
    print("="*60)
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
    except OSError as e:
        if "address already in use" in str(e):
            print(f"\n❌ Port {PORT} busy. Try:")
            print(f"   - Run: `netstat -ano | findstr :{PORT}` to find PID")
            print(f"   - Or change PORT = 8000 → 8001 in code")
        else:
            print("\n❌ Error:", e)