#!/usr/bin/env python3
"""
Simple HTTP server to serve the code flow diagram
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 5001
DIAGRAM_FILE = "code_flow_diagram.html"

class DiagramHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/code_flow_diagram.html'
        return super().do_GET()

def serve_diagram():
    """Serve the code flow diagram"""
    if not Path(DIAGRAM_FILE).exists():
        print(f"Error: {DIAGRAM_FILE} not found!")
        return
    
    print(f"Starting server on port {PORT}")
    print(f"Serving code flow diagram at: http://0.0.0.0:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), DiagramHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    serve_diagram()