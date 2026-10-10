import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from sector_engine import SectorFlowEngine
from anomalies import SectorAnomalyDetector

engine = SectorFlowEngine()
detector = SectorAnomalyDetector()

WEB_DIR = os.path.dirname(os.path.abspath(__file__))

class SectorFlowServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/flows":
            params = parse_qs(parsed.query)
            tf = params.get("timeframe", ["1h"])[0]
            if tf not in ["15m", "1h", "4h"]:
                tf = "1h"

            results = engine.scan_all_sectors(timeframe=tf)
            signals = detector.detect_signals(results)

            payload = {
                "timeframe": tf,
                "timestamp": self.date_time_string(),
                "sectors": results,
                "signals": signals
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            super().do_GET()

def run_server(port=8888):
    server = HTTPServer(("0.0.0.0", port), SectorFlowServer)
    print(f"🚀 Crypto Sector Flow Web Dashboard running at: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    run_server(port)
