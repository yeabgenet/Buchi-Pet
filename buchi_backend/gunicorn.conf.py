"""
gunicorn.conf.py — Production Gunicorn configuration.
Gunicorn manages multiple uvicorn worker processes for concurrency.
"""

import multiprocessing

# Bind address
bind = "0.0.0.0:8000"

# Worker class: uvicorn async workers (required for FastAPI/ASGI)
worker_class = "uvicorn.workers.UvicornWorker"

# Number of workers: (2 × CPU cores) + 1  is the standard formula
workers = multiprocessing.cpu_count() * 2 + 1

# Threads per worker
threads = 2

# Timeout (seconds) — increase for slow DB queries
timeout = 120

# Keep-alive
keepalive = 5

# Logging
accesslog = "-"        # stdout
errorlog = "-"         # stderr
loglevel = "info"

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Graceful timeout
graceful_timeout = 30
