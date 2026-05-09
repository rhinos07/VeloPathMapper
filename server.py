import http.server
import os
import webbrowser

PORT = 8090
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # keine Request-Logs im Terminal

print(f"VeloPathMapper – http://localhost:{PORT}")
print("Zum Beenden: Strg+C")
webbrowser.open(f"http://localhost:{PORT}")

with http.server.HTTPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
