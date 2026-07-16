"""
ElevateIQ — Stats Service
Aggregated statistics for the admin dashboard.
"""
from models.models import db, Admin, Candidate, Assessment, Submission


def get_dashboard_stats() -> dict:
    """Return all stats cards values for the admin dashboard."""
    total_candidates = db.session.query(Candidate).count()
    total_assessments = db.session.query(Assessment).count()
    active_assessments = db.session.query(Assessment).filter_by(status='active').count()
    total_attempts = db.session.query(Submission).filter(
        Submission.status != 'in_progress'
    ).count()
    passed = db.session.query(Submission).filter_by(status='pass').count()
    failed = db.session.query(Submission).filter_by(status='fail').count()
    in_progress = db.session.query(Submission).filter_by(status='in_progress').count()

    return {
        'total_candidates': total_candidates,
        'total_assessments': total_assessments,
        'active_assessments': active_assessments,
        'total_attempts': total_attempts,
        'passed': passed,
        'failed': failed,
        'in_progress': in_progress,
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
