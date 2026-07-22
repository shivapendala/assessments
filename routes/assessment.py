"""
ElevateIQ — Assessment Blueprint
Handles: assessment start, engine page, auto-save, violations,
         submission, and result display.
"""
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session, jsonify
)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.models import db, Assessment, Question, Submission, Answer, Candidate
from utils.helpers import candidate_required, assessment_session_required, api_success, api_error

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')


# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────

@assessment_bp.route('/start', methods=['POST'])
@candidate_required
def start():
    candidate_id = session['candidate_id']
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        session.clear()
        return redirect(url_for('candidate.register'))

    selected_track = session.get('selected_track', 'IT')
    if selected_track == 'Non-IT':
        active_assessment = Assessment.query.filter(Assessment.title.contains('Non-IT')).first()
    else:
        active_assessment = Assessment.query.filter(Assessment.title.contains('IT'), ~Assessment.title.contains('Non-IT')).first()

    if not active_assessment:
        flash('The selected assessment is currently not available.', 'warning')
        return redirect(url_for('candidate.dashboard'))

    # Enforce one-attempt rule
    existing = Submission.query.filter_by(
        candidate_id=candidate_id,
        assessment_id=active_assessment.id
    ).first()

    if existing:
        if existing.status != 'in_progress':
            # Already submitted — redirect to result
            flash('You have already completed this assessment.', 'info')
            return redirect(url_for('assessment.result', submission_id=existing.id))
        else:
            # Resume in-progress
            session['submission_id'] = existing.id
            session['assessment_id'] = active_assessment.id
            return redirect(url_for('assessment.engine'))

    # Create new submission
    total_q = db.session.query(func.count(Question.id)).filter_by(
        assessment_id=active_assessment.id
    ).scalar() or 0
    if total_q == 0:
        flash('This assessment has no questions yet. Contact admin.', 'warning')
        return redirect(url_for('candidate.dashboard'))

    submission = Submission(
        candidate_id=candidate_id,
        assessment_id=active_assessment.id,
        total_questions=total_q,
        status='in_progress',
    )
    db.session.add(submission)
    db.session.commit()

    session['submission_id'] = submission.id
    session['assessment_id'] = active_assessment.id
    return redirect(url_for('assessment.engine'))


# ─────────────────────────────────────────────
# ASSESSMENT ENGINE PAGE
# ─────────────────────────────────────────────

@assessment_bp.route('/')
@assessment_session_required
def engine():
    submission_id = session['submission_id']
    assessment_id = session['assessment_id']

    submission = Submission.query.get(submission_id)
    if not submission or submission.status != 'in_progress':
        flash('Your assessment session is not active.', 'warning')
        return redirect(url_for('candidate.dashboard'))

    assessment = Assessment.query.get(assessment_id)
    candidate = Candidate.query.get(session['candidate_id'])

    questions = Question.query.filter_by(assessment_id=assessment_id).order_by(Question.id).all()
    
    # Shuffle deterministically per candidate to prevent cheating while maintaining reload consistency
    import random
    random.seed(candidate.id)
    random.shuffle(questions)

    # Load saved answers for this submission
    saved_answers = {
        a.question_id: a.selected_option
        for a in Answer.query.filter_by(submission_id=submission_id).all()
    }

    questions_data = [q.to_dict() for q in questions]

    return render_template(
        'candidate/assessment.html',
        assessment=assessment,
        questions=questions,
        questions_data=questions_data,
        saved_answers=saved_answers,
        submission=submission,
        candidate=candidate,
    )


# ─────────────────────────────────────────────
# AUTO-SAVE ANSWER (AJAX)
# ─────────────────────────────────────────────

@assessment_bp.route('/save-answer', methods=['POST'])
@assessment_session_required
def save_answer():
    submission_id = session['submission_id']
    submission = Submission.query.get(submission_id)

    if not submission or submission.status != 'in_progress':
        return api_error('Assessment session expired.', 403)

    data = request.get_json(silent=True) or {}
    question_id = data.get('question_id')
    selected_option = data.get('selected_option')  # A/B/C/D or null

    if not question_id:
        return api_error('Missing question_id.', 400)

    # Validate question belongs to this assessment
    q = Question.query.get(question_id)
    if not q or q.assessment_id != submission.assessment_id:
        return api_error('Invalid question.', 400)

    # Validate selected_option
    if selected_option not in ('A', 'B', 'C', 'D', None):
        return api_error('Invalid option.', 400)

    # Upsert — safe to call multiple times
    try:
        stmt = pg_insert(Answer).values(
            submission_id=submission_id,
            question_id=question_id,
            selected_option=selected_option,
        ).on_conflict_do_update(
            constraint='uq_submission_question',
            set_={'selected_option': selected_option}
        )
        db.session.execute(stmt)
        db.session.commit()
    except Exception:
        # Fallback for SQLite (dev) which doesn't support pg_insert
        db.session.rollback()
        existing = Answer.query.filter_by(
            submission_id=submission_id,
            question_id=question_id
        ).first()
        if existing:
            existing.selected_option = selected_option
        else:
            db.session.add(Answer(
                submission_id=submission_id,
                question_id=question_id,
                selected_option=selected_option
            ))
        db.session.commit()

    return api_success(message='Answer saved.')


# ─────────────────────────────────────────────
# RECORD VIOLATION (AJAX)
# ─────────────────────────────────────────────

@assessment_bp.route('/record-violation', methods=['POST'])
@assessment_session_required
def record_violation():
    submission_id = session['submission_id']
    submission = Submission.query.get(submission_id)

    if not submission or submission.status != 'in_progress':
        return api_error('No active session.', 403)

    submission.violations = (submission.violations or 0) + 1
    db.session.commit()

    auto_submit = submission.violations >= 3
    return api_success(data={
        'violations': submission.violations,
        'auto_submit': auto_submit,
    })


# ─────────────────────────────────────────────
# SUBMIT ASSESSMENT
# ─────────────────────────────────────────────

@assessment_bp.route('/submit', methods=['POST'])
@assessment_session_required
def submit():
    submission_id = session['submission_id']
    submission = Submission.query.get(submission_id)

    if not submission:
        flash('Submission not found.', 'danger')
        return redirect(url_for('candidate.dashboard'))

    if submission.status != 'in_progress':
        # Already submitted
        return redirect(url_for('assessment.result', submission_id=submission.id))

    # Fetch all answers for this submission
    answers = Answer.query.filter_by(submission_id=submission_id).all()
    questions = Question.query.filter_by(
        assessment_id=submission.assessment_id
    ).all()

    answer_map = {a.question_id: a.selected_option for a in answers}
    correct = sum(
        1 for q in questions
        if answer_map.get(q.id) == q.correct_answer
    )
    total = len(questions)
    percentage = (correct / total * 100) if total > 0 else 0
    pass_pct = submission.assessment.pass_percentage
    status = 'pass' if percentage >= pass_pct else 'fail'

    submission.score = correct
    submission.total_questions = total
    submission.percentage = percentage
    submission.status = status
    submission.submitted_at = datetime.utcnow()
    db.session.commit()

    # Clear assessment from session (keep candidate session)
    session.pop('submission_id', None)
    session.pop('assessment_id', None)

    return redirect(url_for('assessment.result', submission_id=submission.id))


# ─────────────────────────────────────────────
# RESULT PAGE
# ─────────────────────────────────────────────

@assessment_bp.route('/result/<int:submission_id>')
def result(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    # Security: only the owning candidate (or admin) can view
    candidate_id_in_session = session.get('candidate_id')
    if candidate_id_in_session != submission.candidate_id:
        # Allow if admin is logged in
        from flask_login import current_user
        if not current_user.is_authenticated:
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('candidate.register'))

    questions = Question.query.filter_by(
        assessment_id=submission.assessment_id
    ).all()
    answers = {a.question_id: a.selected_option for a in
               Answer.query.filter_by(submission_id=submission_id).all()}

    wrong = sum(
        1 for q in questions
        if q.id in answers and answers[q.id] and answers[q.id] != q.correct_answer
    )
    unanswered = sum(1 for q in questions if not answers.get(q.id))

    return render_template(
        'candidate/result.html',
        submission=submission,
        candidate=submission.candidate,
        assessment=submission.assessment,
        wrong=wrong,
        unanswered=unanswered,
    )
