# ElevateIQ — Gunicorn Production Configuration
import multiprocessing
import os

# ── Binding ──────────────────────────────────────────────────
bind = os.environ.get('BIND', '0.0.0.0:8000')

# ── Workers ──────────────────────────────────────────────────
# Rule of thumb: (2 × CPU cores) + 1
workers = int(os.environ.get('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'gevent'          # async workers for concurrent connections
worker_connections = 1000        # max simultaneous connections per worker
threads = 2

# ── Timeouts ─────────────────────────────────────────────────
timeout = 120          # seconds before killing a silent worker
keepalive = 5          # keep-alive seconds
graceful_timeout = 30  # wait for requests to finish on reload/shutdown

# ── Logging ──────────────────────────────────────────────────
loglevel = 'info'
accesslog = '-'        # stdout
errorlog  = '-'        # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Process ──────────────────────────────────────────────────
preload_app  = True    # load app before forking (saves memory)
daemon       = False   # systemd manages the process
proc_name    = 'elevateiq'
pidfile      = '/tmp/elevateiq.pid'

# ── Reload (development only) ─────────────────────────────────
# reload = True
