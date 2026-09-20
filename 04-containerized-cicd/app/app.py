import http.server
import socket
import os

HOSTNAME = socket.gethostname()
VERSION = os.environ.get('APP_VERSION', 'v1')

def render_page():
    return f"""<!DOCTYPE html>
<html>
<head>
<title>Containerized App</title>
<style>
  body {{ font-family: Arial; background: #0f1117; color: #e0e0e0; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
  .card {{ background: #1a1f2e; border: 1px solid #2a2f3e; border-radius: 12px; padding: 40px; text-align: center; max-width: 500px; width: 90%; }}
  h1 {{ color: #FF9900; margin-bottom: 8px; }}
  .subtitle {{ color: #888; margin-bottom: 30px; font-size: 14px; }}
  .info {{ background: #232f3e; border-radius: 8px; padding: 16px; margin: 10px 0; text-align: left; }}
  .label {{ color: #FF9900; font-size: 12px; font-weight: bold; }}
  .value {{ color: #fff; font-size: 14px; margin-top: 4px; font-family: monospace; }}
  .badge {{ display: inline-block; background: #FF9900; color: #0f1117; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
  <h1>ECS Container</h1>
  <p class="subtitle">Running on Amazon ECS - EC2 Launch Type</p>
  <div class="info">
    <div class="label">CONTAINER ID</div>
    <div class="value">{HOSTNAME}</div>
  </div>
  <div class="info">
    <div class="label">VERSION</div>
    <div class="value">{VERSION}</div>
  </div>
  <div class="info">
    <div class="label">DEPLOYED VIA</div>
    <div class="value">CodePipeline -&gt; CodeBuild -&gt; ECR -&gt; ECS</div>
  </div>
  <span class="badge">HEALTHY</span>
</div>
</body>
</html>"""

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
