#!/usr/bin/env python3
import http.server
import json
import urllib.parse
import urllib.request
import os
import sys

# RDS connection via pymysql - installed on EC2 via UserData
# Locally this import fails gracefully
try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

# DynamoDB via boto3 - installed on EC2 via UserData
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

RDS_HOST = os.environ.get('RDS_HOST', 'localhost')
RDS_USER = os.environ.get('RDS_USER', 'admin')
RDS_PASSWORD = os.environ.get('RDS_PASSWORD', '')
RDS_DB = os.environ.get('RDS_DB', 'usersdb')
DYNAMO_TABLE = os.environ.get('DYNAMO_TABLE', 'users')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')


def get_rds_connection():
    return pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DB,
        connect_timeout=5
    )


def rds_add(name, email):
    if not PYMYSQL_AVAILABLE:
        return False, 'pymysql not available (local mode)'
    try:
        conn = get_rds_connection()
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (name, email) VALUES (%s, %s)',
                (name, email)
            )
        conn.commit()
        conn.close()
        return True, f'Added {name} to RDS MySQL'
    except Exception as e:
        return False, str(e)


def rds_get():
    if not PYMYSQL_AVAILABLE:
        return []
    try:
        conn = get_rds_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, email FROM users ORDER BY id DESC LIMIT 10')
            rows = cur.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'email': r[2]} for r in rows]
    except Exception as e:
        return [{'error': str(e)}]


def dynamo_add(name, email):
    if not BOTO3_AVAILABLE:
        return False, 'boto3 not available (local mode)'
    try:
        table = boto3.resource('dynamodb', region_name=AWS_REGION).Table(DYNAMO_TABLE)
        import time
        table.put_item(Item={
            'user_id': str(int(time.time() * 1000)),
            'name': name,
            'email': email
        })
        return True, f'Added {name} to DynamoDB'
    except Exception as e:
        return False, str(e)


def dynamo_get():
    if not BOTO3_AVAILABLE:
        return []
    try:
        table = boto3.resource('dynamodb', region_name=AWS_REGION).Table(DYNAMO_TABLE)
        result = table.scan(Limit=10)
        return result.get('Items', [])
    except Exception as e:
        return [{'error': str(e)}]


def render_page(rds_rows, dynamo_rows, message=''):
    rds_html = ''.join(
        f'<tr><td>{r.get("id","")}</td><td>{r.get("name","")}</td><td>{r.get("email","")}</td></tr>'
        if 'error' not in r else f'<tr><td colspan="3" style="color:red">{r["error"]}</td></tr>'
        for r in rds_rows
    ) or '<tr><td colspan="3">No data</td></tr>'

    dynamo_html = ''.join(
        f'<tr><td>{r.get("user_id","")}</td><td>{r.get("name","")}</td><td>{r.get("email","")}</td></tr>'
        if 'error' not in r else f'<tr><td colspan="3" style="color:red">{r["error"]}</td></tr>'
        for r in dynamo_rows
    ) or '<tr><td colspan="3">No data</td></tr>'

    msg_html = f'<p style="color:green;font-weight:bold">{message}</p>' if message else ''

    return f"""<!DOCTYPE html>
<html>
<head>
<title>RDS vs DynamoDB</title>
<style>
  body {{ font-family: Arial; padding: 30px; background: #f5f5f5; }}
  h1 {{ color: #232F3E; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
  .box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
  .box h2 {{ margin-top: 0; }}
  .rds h2 {{ color: #1a73e8; }}
  .dynamo h2 {{ color: #FF9900; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #f0f0f0; padding: 6px; text-align: left; }}
  td {{ padding: 6px; border-bottom: 1px solid #eee; }}
  .form {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
  input {{ padding: 6px; margin: 4px; border: 1px solid #ccc; border-radius: 4px; }}
  button {{ padding: 6px 14px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; color: white; }}
  .btn-rds {{ background: #1a73e8; }}
  .btn-dynamo {{ background: #FF9900; }}
  .label {{ font-size: 11px; color: #666; margin-top: 8px; }}
</style>
</head>
<body>
<h1>RDS MySQL vs DynamoDB - Same App, Two Backends</h1>
{msg_html}
<div class="form">
  <strong>Add a user:</strong><br>
  <input type="text" id="name" placeholder="Name">
  <input type="text" id="email" placeholder="Email">
  <button class="btn-rds" onclick="addUser('rds')">Add to RDS MySQL</button>
  <button class="btn-dynamo" onclick="addUser('dynamo')">Add to DynamoDB</button>
  <div class="label">RDS: requires schema (id, name, email columns must exist) &nbsp;|&nbsp; DynamoDB: schemaless, any fields accepted</div>
</div>
<div class="grid">
  <div class="box rds">
    <h2>RDS MySQL</h2>
    <p style="font-size:12px;color:#666">Structured - SQL - Schema enforced - Multi-AZ capable</p>
    <table><tr><th>ID</th><th>Name</th><th>Email</th></tr>{rds_html}</table>
  </div>
  <div class="box dynamo">
    <h2>DynamoDB</h2>
    <p style="font-size:12px;color:#666">Schemaless - NoSQL - Key-Value - Auto-scales</p>
    <table><tr><th>user_id</th><th>Name</th><th>Email</th></tr>{dynamo_html}</table>
  </div>
</div>
<script>
function addUser(backend) {{
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  if (!name || !email) {{ alert('Fill in both fields'); return; }}
  window.location.href = '/add?backend=' + backend + '&name=' + encodeURIComponent(name) + '&email=' + encodeURIComponent(email);
}}
</script>
</body>
</html>"""


class AppHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        message = ''
        if parsed.path == '/add':
            backend = params.get('backend', [''])[0]
            name = params.get('name', [''])[0]
            email = params.get('email', [''])[0]
            if backend == 'rds':
                ok, msg = rds_add(name, email)
            else:
                ok, msg = dynamo_add(name, email)
            message = msg

        if parsed.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            return

        rds_rows = rds_get()
        dynamo_rows = dynamo_get()
        html = render_page(rds_rows, dynamo_rows, message)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f'Starting on port {port}')
    http.server.HTTPServer(('0.0.0.0', port), AppHandler).serve_forever()
