# ElevateIQ — Gunicorn Production Configuration (Optimised)
import multiprocessing
import os

# ── Binding ──────────────────────────────────────────────────
bind = os.environ.get('BIND', '0.0.0.0:8000')

# ── Workers ──────────────────────────────────────────────────
# 8 gevent async workers × 2000 connections = 16,000 max concurrent connections
workers = int(os.environ.get('WORKERS', 8))
worker_class = 'gevent'
worker_connections = int(os.environ.get('WORKER_CONNECTIONS', 2000))

# ── Max Requests (prevents memory leaks in long-running workers) ─────────────
# Workers are recycled after this many requests (+ random jitter to avoid
# thundering-herd restarts hitting the DB simultaneously).
max_requests        = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', 100))

# ── Timeouts ─────────────────────────────────────────────────
timeout = 60           # Reduced from 120s — kill hung workers faster
keepalive = 5          # keep-alive seconds
graceful_timeout = 30  # wait for requests to finish on reload/shutdown

# ── Logging ──────────────────────────────────────────────────
loglevel = 'warning'   # 'info' logs every request; use 'warning' in prod for less I/O
accesslog = '-'        # stdout
errorlog  = '-'        # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Process ──────────────────────────────────────────────────
preload_app  = False   # Set to False for gevent async DB pool isolation across workers
daemon       = False   # systemd manages the process
proc_name    = 'elevateiq'
pidfile      = '/tmp/elevateiq.pid'

# ── Worker tmp dir on tmpfs (faster IPC heartbeat on Linux) ──────────────────
# Uses RAM-backed /dev/shm instead of disk for worker heartbeat files.
worker_tmp_dir = '/dev/shm'

# ── Reload (development only) ─────────────────────────────────
# reload = True
