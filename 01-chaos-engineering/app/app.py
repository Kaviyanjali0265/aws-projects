#!/usr/bin/env python3
import http.server
import urllib.request
from datetime import datetime


def get_instance_id():
    try:
        token_req = urllib.request.Request(
            'http://169.254.169.254/latest/api/token',
            headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'},
            method='PUT'
        )
        token = urllib.request.urlopen(token_req, timeout=2).read().decode()
        id_req = urllib.request.Request(
            'http://169.254.169.254/latest/meta-data/instance-id',
            headers={'X-aws-ec2-metadata-token': token}
        )
        return urllib.request.urlopen(id_req, timeout=2).read().decode()
    except Exception:
        return 'local-machine'


INSTANCE_ID = get_instance_id()


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

        html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial; text-align: center; padding: 60px; background: #f5f5f5;">
    <h1 style="color: #FF9900;">Chaos Engineering Demo</h1>
    <div style="background: white; padding: 30px; border-radius: 10px;
                display: inline-block; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h2>Serving from Instance:</h2>
        <h2 style="color: #232F3E;">{INSTANCE_ID}</h2>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr/>
        <p><em>Keep refreshing - ALB sends you to different instances!</em></p>
        <p><em>When chaos Lambda kills this instance, ASG auto-recovers it.</em></p>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print(f'Starting on port 8080 - Instance: {INSTANCE_ID}')
    http.server.HTTPServer(('0.0.0.0', 8080), AppHandler).serve_forever()
