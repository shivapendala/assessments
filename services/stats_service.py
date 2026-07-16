"""
ElevateIQ — Stats Service
Aggregated statistics for the admin dashboard.

Performance: Consolidated from 7 separate COUNT queries into 2 queries
using SQLAlchemy aggregate functions (func.count + case).
Results are cached for 5 minutes via Flask-Caching.
"""
from sqlalchemy import func, case
from models.models import db, Candidate, Assessment, Question, Submission
from extensions import cache


def get_dashboard_stats() -> dict:
    """Return all stats card values for the admin dashboard.

    Cached for 5 minutes (CACHE_DEFAULT_TIMEOUT).
    Uses 2 DB queries instead of the previous 7:
      1. COUNT candidates + COUNT assessments + COUNT active assessments
      2. GROUP BY status on submissions to get all status counts in one pass
    """
    return _compute_dashboard_stats()


@cache.cached(timeout=300, key_prefix='dashboard_stats')
def _compute_dashboard_stats() -> dict:
    # ── Query 1: candidates + assessments in one shot ─────────
    candidate_count = db.session.query(func.count(Candidate.id)).scalar() or 0
    assessment_stats = db.session.query(
        func.count(Assessment.id).label('total'),
        func.sum(case((Assessment.status == 'active', 1), else_=0)).label('active'),
    ).one()
    total_assessments = assessment_stats.total or 0
    active_assessments = int(assessment_stats.active or 0)

    # ── Query 2: all submission status counts in a single GROUP BY ──
    status_rows = (
        db.session.query(
            Submission.status,
            func.count(Submission.id).label('cnt')
        )
        .group_by(Submission.status)
        .all()
    )

    status_counts = {row.status: row.cnt for row in status_rows}
    passed      = status_counts.get('pass', 0)
    failed      = status_counts.get('fail', 0)
    in_progress = status_counts.get('in_progress', 0)
    total_attempts = passed + failed  # excludes in_progress (same as before)

    return {
        'total_candidates':  candidate_count,
        'total_assessments': total_assessments,
        'active_assessments': active_assessments,
        'total_attempts':    total_attempts,
        'passed':            passed,
        'failed':            failed,
        'in_progress':       in_progress,
        'pass_rate': round((passed / total_attempts * 100) if total_attempts > 0 else 0, 1),
    }


def get_recent_results(limit: int = 10):
    """Return the most recent completed submissions."""
    return (
        db.session.query(Submission)
        .filter(Submission.status != 'in_progress')
        .order_by(Submission.submitted_at.desc())
        .limit(limit)
        .all()
    )
