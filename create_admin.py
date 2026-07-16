"""
create_admin.py — Standalone script to create the default admin.
Run with: python create_admin.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, _create_default_admin

if __name__ == '__main__':
    application = create_app()
    _create_default_admin(application)
