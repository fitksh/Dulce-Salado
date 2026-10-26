"""Small WSGI deployment for the shared Raspberry Pi (Python 3.12/ARM64)."""

bind = "0.0.0.0:8000"
workers = 2
worker_class = "gthread"
threads = 2
timeout = 60
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
worker_tmp_dir = "/tmp"
errorlog = "-"
# Order URLs contain private bearer tokens. Do not put request paths in logs.
accesslog = None
# Django trusts only the header Nginx overwrites; Gunicorn adds no separate trust.
forwarded_allow_ips = ""
secure_scheme_headers = {}
