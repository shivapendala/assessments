"""
ElevateIQ — Utility Helpers
Input validation, sanitization, and other shared utilities.
"""
import re
import html
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify


# ─────────────────────────────────────────────
# Validators
# ─────────────────────────────────────────────

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
HALL_TICKET_RE = re.compile(r'^[A-Za-z0-9\-_/]{3,50}$')


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_RE.match(email.strip()))


def is_valid_hall_ticket(ht: str) -> bool:
    """Validate hall ticket — alphanumeric with optional dash/underscore/slash, 3–50 chars."""
    return bool(HALL_TICKET_RE.match(ht.strip()))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip and HTML-escape a string, truncate to max_length."""
    return html.escape(value.strip())[:max_length]


# ─────────────────────────────────────────────
# Candidate Session Guard
# ─────────────────────────────────────────────

def candidate_required(f):
    """Decorator: require a logged-in candidate session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please register first.', 'warning')
            return redirect(url_for('candidate.register'))
        return f(*args, **kwargs)
    return decorated


def assessment_session_required(f):
    """Decorator: require an active assessment session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session or 'submission_id' not in session:
            flash('No active assessment session. Please start from your dashboard.', 'warning')
            return redirect(url_for('candidate.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# JSON API helpers
# ─────────────────────────────────────────────

def api_success(data=None, message='Success', status=200):
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status


def api_error(message='An error occurred', status=400):
    return jsonify({'success': False, 'message': message}), status


# ─────────────────────────────────────────────
# Pagination helper
# ─────────────────────────────────────────────

def paginate_query(query, page: int, per_page: int = 20):
    """Return paginated results with metadata."""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }
