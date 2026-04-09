#!/usr/bin/env python3
"""简单的本地服务器用于测试 JobMatchAI"""
import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加 CORS 头（如果需要）
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"📂 Serving at http://localhost:{PORT}")
    print(f"📁 Directory: {DIRECTORY}")
    print(f"\n💡 如果你设置了 API Key，访问: http://localhost:{PORT}/?api_key=YOUR_KEY_HERE")
    print("\n按 Ctrl+C 停止服务器")
    httpd.serve_forever()
