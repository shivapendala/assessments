"""
ElevateIQ — Candidate Blueprint
Handles: registration, candidate dashboard.
"""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session
)
from sqlalchemy.exc import IntegrityError

from models.models import db, Candidate, Assessment, Submission
from utils.helpers import (
    is_valid_email, is_valid_hall_ticket, sanitize_string, candidate_required
)

candidate_bp = Blueprint('candidate', __name__)


def _get_active_assessments():
    """Return active assessments, cached for 60 seconds."""
    from extensions import cache
    cache_key = 'active_assessments'
    result = cache.get(cache_key)
    if result is None:
        result = Assessment.query.filter_by(status='active').all()
        cache.set(cache_key, result, timeout=60)
    return result


@candidate_bp.route('/')
def index():
    if 'candidate_id' in session:
        return redirect(url_for('candidate.dashboard'))
    return render_template('candidate/home.html')


@candidate_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.args.get('logout') == '1':
        session.clear()

    # If candidate already in session on GET request, redirect to dashboard unless switching accounts
    if request.method == 'GET' and 'candidate_id' in session and not request.args.get('switch'):
        return redirect(url_for('candidate.dashboard'))

    if request.method == 'POST':
        full_name = sanitize_string(request.form.get('full_name', ''))
        email = request.form.get('email', '').strip().lower()
        hall_ticket = request.form.get('hall_ticket', '').strip().upper()

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not is_valid_email(email):
            errors.append('Please enter a valid email address.')
        if not is_valid_hall_ticket(hall_ticket):
            errors.append('Hall Ticket must be 3–50 alphanumeric characters (- _ / allowed).')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('candidate/register.html',
                                   full_name=full_name, email=email, hall_ticket=hall_ticket)

        # Single query check for existing candidate by email or hall ticket
        matches = Candidate.query.filter(
            db.or_(Candidate.email == email, Candidate.hall_ticket == hall_ticket)
        ).all()

        existing_by_email = next((c for c in matches if c.email == email), None)
        existing_by_ht    = next((c for c in matches if c.hall_ticket == hall_ticket), None)

        if existing_by_email:
            if existing_by_email.hall_ticket == hall_ticket:
                # Login existing student instantly
                session.clear()
                session.permanent = True
                session['candidate_id'] = existing_by_email.id
                session['candidate_name'] = existing_by_email.full_name
                session['hall_ticket'] = existing_by_email.hall_ticket
                flash(f'Welcome back, {existing_by_email.full_name}!', 'info')
                return redirect(url_for('candidate.dashboard'))
            else:
                flash('This email is already registered with a different Hall Ticket.', 'danger')
                return render_template('candidate/register.html',
                                       full_name=full_name, email=email, hall_ticket=hall_ticket)

        if existing_by_ht:
            flash('This Hall Ticket is already registered under a different email address.', 'danger')
            return render_template('candidate/register.html',
                                   full_name=full_name, email=email, hall_ticket=hall_ticket)

        # Check if there's an active assessment (cached — no DB hit)
        active_assessments = _get_active_assessments()
        if not active_assessments:
            flash('No active assessment is currently available. Please check back later.', 'warning')
            return render_template('candidate/register.html',
                                   full_name=full_name, email=email, hall_ticket=hall_ticket)

        try:
            candidate = Candidate(
                full_name=full_name,
                email=email,
                hall_ticket=hall_ticket,
            )
            db.session.add(candidate)
            db.session.commit()

            # Purge any stale session data before setting new session
            session.clear()
            session.permanent = True
            session['candidate_id'] = candidate.id
            session['candidate_name'] = candidate.full_name
            session['hall_ticket'] = candidate.hall_ticket

            flash(f'Registration successful! Welcome, {full_name}!', 'success')
            return redirect(url_for('candidate.dashboard'))

        except Exception as err:
            db.session.rollback()
            flash(f'Registration failed: {str(err)}', 'danger')

    return render_template('candidate/register.html')


@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    candidate_id = session['candidate_id']
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        session.clear()
        return redirect(url_for('candidate.register'))

    # Single query to fetch all submissions for this candidate (consolidates 2 queries into 1)
    user_submissions = Submission.query.filter_by(candidate_id=candidate_id).all()

    # Force single attempt limit: redirect to results page if completed
    completed_sub = next((s for s in user_submissions if s.status != 'in_progress'), None)
    if completed_sub:
        return redirect(url_for('assessment.result', submission_id=completed_sub.id))

    selected_track = session.get('selected_track')

    if not selected_track:
        # Show track selection screen
        return render_template(
            'candidate/dashboard.html',
            candidate=candidate,
            show_selection=True
        )

    # Fetch corresponding active assessment based on selected track (cached — no DB hit)
    all_assessments = _get_active_assessments()
    if selected_track == 'Non-IT':
        assessment = next((a for a in all_assessments if 'Non-IT' in a.title), None)
    else:
        assessment = next((a for a in all_assessments if 'IT' in a.title and 'Non-IT' not in a.title), None)
    if not assessment and all_assessments:
        assessment = all_assessments[0]

    # Check if already attempted (from pre-fetched list — zero extra DB queries)
    existing_submission = None
    if assessment:
        existing_submission = next((s for s in user_submissions if s.assessment_id == assessment.id), None)

    return render_template(
        'candidate/dashboard.html',
        candidate=candidate,
        assessment=assessment,
        existing_submission=existing_submission,
        selected_track=selected_track,
        show_selection=False
    )


@candidate_bp.route('/select-track', methods=['POST'])
@candidate_required
def select_track():
    candidate_id = session['candidate_id']
    # Block track selection if they have any submission in progress or completed
    existing = Submission.query.filter_by(candidate_id=candidate_id).first()
    if existing:
        flash('You already have an active or completed assessment session.', 'warning')
        return redirect(url_for('candidate.dashboard'))

    track = request.form.get('track', 'IT')
    if track not in ('IT', 'Non-IT'):
        track = 'IT'
    session['selected_track'] = track
    return redirect(url_for('candidate.dashboard'))


@candidate_bp.route('/change-track', methods=['POST'])
@candidate_required
def change_track():
    candidate_id = session['candidate_id']
    # If they already have an in-progress submission, block changing track
    in_progress = Submission.query.filter_by(candidate_id=candidate_id, status='in_progress').first()
    if in_progress:
        flash('Cannot change track while an assessment is in progress.', 'danger')
        return redirect(url_for('candidate.dashboard'))
    session.pop('selected_track', None)
    return redirect(url_for('candidate.dashboard'))


@candidate_bp.route('/candidate/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('candidate.register'))
