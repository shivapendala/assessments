from app import csrf
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

    user_submissions = Submission.query.filter_by(candidate_id=candidate_id).all()

    sub_round1 = next((s for s in user_submissions if s.assessment_id in (1, 2, 3) and s.status != 'in_progress'), None)
    sub_round2 = next((s for s in user_submissions if s.assessment_id == 4 and s.status != 'in_progress'), None)

    in_prog_round1 = next((s for s in user_submissions if s.assessment_id in (1, 2, 3) and s.status == 'in_progress'), None)
    in_prog_round2 = next((s for s in user_submissions if s.assessment_id == 4 and s.status == 'in_progress'), None)

    round1_assessments = Assessment.query.filter(Assessment.id.in_([1, 2, 3]), Assessment.status == 'active').order_by(Assessment.id).all()

    return render_template(
        'candidate/dashboard.html',
        candidate=candidate,
        sub_round1=sub_round1,
        sub_round2=sub_round2,
        in_prog_round1=in_prog_round1,
        in_prog_round2=in_prog_round2,
        round1_assessments=round1_assessments
    )


@candidate_bp.route('/select-track', methods=['POST'])
@candidate_required
def select_track():
    candidate_id = session['candidate_id']
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


@candidate_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        hall_ticket = request.form.get('hall_ticket', '').strip().upper()
        email = request.form.get('email', '').strip().lower()

        candidate = None
        if hall_ticket:
            candidate = Candidate.query.filter_by(hall_ticket=hall_ticket).first()
        elif email:
            candidate = Candidate.query.filter_by(email=email).first()

        if candidate:
            session['candidate_id'] = candidate.id
            flash(f'Welcome back, {candidate.full_name}!', 'success')
            return redirect(url_for('candidate.dashboard'))
        else:
            flash('Candidate not found with this Hall Ticket/Email. Please check your credentials or register.', 'danger')

    return render_template('candidate/login.html')
