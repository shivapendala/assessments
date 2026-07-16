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


@candidate_bp.route('/')
def index():
    if 'candidate_id' in session:
        return redirect(url_for('candidate.dashboard'))
    return render_template('candidate/home.html')


@candidate_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If candidate already in session, go to dashboard
    if 'candidate_id' in session:
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

        # Check uniqueness
        if Candidate.query.filter_by(email=email).first():
            flash('This email is already registered. Contact admin if this is an error.', 'danger')
            return render_template('candidate/register.html',
                                   full_name=full_name, email=email, hall_ticket=hall_ticket)

        if Candidate.query.filter_by(hall_ticket=hall_ticket).first():
            flash('This Hall Ticket is already registered.', 'danger')
            return render_template('candidate/register.html',
                                   full_name=full_name, email=email, hall_ticket=hall_ticket)

        # Check if there's an active assessment
        active_assessment = Assessment.query.filter_by(status='active').first()
        if not active_assessment:
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

            # Store in session
            session.permanent = True
            session['candidate_id'] = candidate.id
            session['candidate_name'] = candidate.full_name
            session['hall_ticket'] = candidate.hall_ticket

            flash(f'Registration successful! Welcome, {full_name}!', 'success')
            return redirect(url_for('candidate.dashboard'))

        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Email or Hall Ticket already exists.', 'danger')

    return render_template('candidate/register.html')


@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    candidate = Candidate.query.get(session['candidate_id'])
    if not candidate:
        session.clear()
        return redirect(url_for('candidate.register'))

    # Force single attempt limit: redirect to results page if they have any completed submission
    completed_sub = Submission.query.filter(
        Submission.candidate_id == candidate.id,
        Submission.status != 'in_progress'
    ).first()
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

    # Fetch corresponding assessment based on selected track
    if selected_track == 'Non-IT':
        assessment = Assessment.query.filter(Assessment.title.like('%Non-IT%')).first()
    else:
        assessment = Assessment.query.filter(Assessment.title.like('%IT%'), ~Assessment.title.like('%Non-IT%')).first()

    # Check if already attempted
    existing_submission = None
    if assessment:
        existing_submission = Submission.query.filter_by(
            candidate_id=candidate.id,
            assessment_id=assessment.id
        ).first()

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
