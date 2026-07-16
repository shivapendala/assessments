"""
ElevateIQ — Shared extension instances
Defined here to avoid circular imports between app.py and service modules.
"""
from flask_caching import Cache

cache = Cache()
