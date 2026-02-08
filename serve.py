"""
Simple HTTP server to serve the dashboard and cache pages with proper file access.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow fetch() from HTML pages
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Add cache control headers
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Log all requests including what files are being served
        print(f"[{self.log_date_time_string()}] {format%args}")

def start_server():
    """Start the HTTP server and open the dashboard in a browser."""
    handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"\n✓ Server running at http://localhost:{PORT}")
        print(f"✓ Dashboard: {url}")
        print(f"✓ Components Cache: http://localhost:{PORT}/components_cache.html")
        print(f"✓ Press Ctrl+C to stop\n")
        
        # Open dashboard in browser
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Server stopped")

if __name__ == "__main__":
    start_server()
