import http.server
import socket
import os

HOSTNAME = socket.gethostname()
VERSION = os.environ.get('APP_VERSION', 'v1')

with open(os.path.join(os.path.dirname(__file__), 'templates/index.html')) as f:
    TEMPLATE = f.read()

def render_page():
    return TEMPLATE.replace('{{HOSTNAME}}', HOSTNAME).replace('{{VERSION}}', VERSION)

class AppHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(render_page().encode())

    def log_message(self, *a):
        pass

http.server.HTTPServer(('0.0.0.0', 80), AppHandler).serve_forever()
