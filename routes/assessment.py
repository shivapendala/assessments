"""
ElevateIQ — Assessment Blueprint
Handles: assessment start, engine page, auto-save, violations,
         submission, and result display.
"""
import random
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session, jsonify
)
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.models import db, Assessment, Question, Submission, Answer, Candidate, CodingProblem, CodingTestCase, CodingSubmission
from utils.code_sandbox import execute_testcase, execute_testcase_suite
from utils.helpers import candidate_required, assessment_session_required, api_success, api_error

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')


def _get_cached_questions(assessment_id: int):
    from extensions import cache
    cache_key = f'questions_assessment_{assessment_id}'
    questions = cache.get(cache_key)
    if questions is None:
        questions = Question.query.filter_by(assessment_id=assessment_id).order_by(Question.id).all()
        cache.set(cache_key, questions, timeout=300)
    return questions


# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────

@assessment_bp.route('/start', methods=['POST'])
@candidate_required
def start():
    candidate_id = session['candidate_id']
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        session.clear()
        return redirect(url_for('candidate.register'))

    target_drive_id = request.form.get('assessment_id', type=int) or session.get('selected_assessment_id')
    from routes.candidate import _get_active_assessments
    all_assessments = _get_active_assessments()

    if target_drive_id:
        active_assessment = db.session.get(Assessment, target_drive_id)
    else:
        selected_track = session.get('selected_track', 'IT')
        if selected_track == 'Non-IT':
            active_assessment = next((a for a in all_assessments if 'Non-IT' in a.title), None)
        else:
            active_assessment = next((a for a in all_assessments if 'IT' in a.title and 'Non-IT' not in a.title), None)
        if not active_assessment and all_assessments:
            active_assessment = all_assessments[0]

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

    submission = db.session.get(Submission, submission_id)
    if not submission or submission.status != 'in_progress':
        flash('Your assessment session is not active.', 'warning')
        return redirect(url_for('candidate.dashboard'))

    assessment = db.session.get(Assessment, assessment_id)
    candidate = db.session.get(Candidate, session['candidate_id'])

    # Use cached questions instead of a fresh DB query
    questions = _get_cached_questions(assessment_id)
    
    # Jumble question order deterministically per candidate session (thread-safe)
    rng = random.Random(f"sub_{submission_id}_cand_{candidate.id}")
    shuffled_questions = list(questions)  # copy to avoid mutating cache
    rng.shuffle(shuffled_questions)

    # Load saved answers for this submission
    saved_answers = {
        a.question_id: a.selected_option
        for a in Answer.query.filter_by(submission_id=submission_id).all()
    }

    # Build questions_data with jumbled options for each question
    questions_data = []
    for q in shuffled_questions:
        q_dict = q.to_dict()
        opts = [
            {'key': 'A', 'text': q.option_a},
            {'key': 'B', 'text': q.option_b},
            {'key': 'C', 'text': q.option_c},
            {'key': 'D', 'text': q.option_d},
        ]
        q_rng = random.Random(f"sub_{submission_id}_q_{q.id}")
        q_rng.shuffle(opts)
        q_dict['options'] = opts
        questions_data.append(q_dict)

    # Fetch Coding Problems for Section 2 (Assessment-specific or Global)
    coding_problems = CodingProblem.query.filter(
        db.or_(CodingProblem.assessment_id == assessment_id, CodingProblem.assessment_id.is_(None))
    ).order_by(CodingProblem.id).all()

    coding_problems_data = []
    for p in coding_problems:
        p_dict = p.to_dict()
        # Find any saved submission for this problem
        saved_sub = CodingSubmission.query.filter_by(
            submission_id=submission_id,
            problem_id=p.id
        ).first()
        p_dict['saved_submission'] = saved_sub.to_dict() if saved_sub else None
        coding_problems_data.append(p_dict)

    return render_template(
        'candidate/assessment.html',
        assessment=assessment,
        questions=shuffled_questions,
        questions_data=questions_data,
        saved_answers=saved_answers,
        coding_problems=coding_problems_data,
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
    submission = db.session.get(Submission, submission_id)

    if not submission or submission.status != 'in_progress':
        return api_error('Assessment session expired.', 403)

    data = request.get_json(silent=True) or {}
    
    # Support both bulk payload { answers: { "10": "A", "11": "B" } } and single payload { question_id: 10, selected_option: "A" }
    answers_to_save = {}
    if 'answers' in data and isinstance(data['answers'], dict):
        answers_to_save = data['answers']
    elif 'question_id' in data:
        answers_to_save[str(data['question_id'])] = data.get('selected_option')

    if not answers_to_save:
        return api_error('Missing answer data.', 400)

    try:
        # Prepare list of records for bulk multi-row upsert
        records = []
        for q_id_str, selected_option in answers_to_save.items():
            try:
                question_id = int(q_id_str)
            except (ValueError, TypeError):
                continue

            if selected_option in ('A', 'B', 'C', 'D', None):
                records.append({
                    'submission_id': submission_id,
                    'question_id': question_id,
                    'selected_option': selected_option
                })

        if records:
            is_postgres = 'postgresql' in str(db.engine.url)
            if is_postgres:
                # Single multi-row bulk upsert query (1 SQL statement instead of N statements)
                stmt = pg_insert(Answer).values(records)
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_assessment_submission_question',
                    set_={'selected_option': stmt.excluded.selected_option}
                )
                db.session.execute(stmt)
            else:
                for r in records:
                    existing = Answer.query.filter_by(
                        submission_id=r['submission_id'],
                        question_id=r['question_id']
                    ).first()
                    if existing:
                        existing.selected_option = r['selected_option']
                    else:
                        db.session.add(Answer(**r))

        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return api_error('Failed to save answers.', 500)

    return api_success(message='Answers saved.')


# ─────────────────────────────────────────────
# RECORD VIOLATION (AJAX)
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# LIVE CODING SANDBOX (AJAX RUN & SUBMIT)
# ─────────────────────────────────────────────

@assessment_bp.route('/code/run', methods=['POST'])
@assessment_session_required
def run_code():
    """Execute candidate code against sample testcases or custom input."""
    submission_id = session.get('submission_id')
    submission = db.session.get(Submission, submission_id)
    if not submission or submission.status != 'in_progress':
        return api_error('Assessment session expired or inactive.', 403)

    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    language = (data.get('language') or 'python').strip()
    source_code = data.get('source_code') or ''
    custom_input = data.get('custom_input')

    if not source_code:
        return api_error('Source code is required.', 400)

    if custom_input is not None:
        res = execute_testcase(source_code, language, custom_input, expected_output=None)
        return jsonify({
            'mode': 'custom',
            'status': res['status'],
            'passed': res['passed'],
            'actual_output': res['actual_output'],
            'stderr': res['stderr'],
            'execution_time_ms': res['execution_time_ms'],
            'error': res['error']
        }), 200

    # Fetch public sample testcases
    sample_cases = CodingTestCase.query.filter_by(
        problem_id=problem_id,
        is_hidden=False
    ).order_by(CodingTestCase.id).all()

    if not sample_cases:
        res = execute_testcase(source_code, language, '', expected_output=None)
        return jsonify({
            'mode': 'empty',
            'status': res['status'],
            'actual_output': res['actual_output'],
            'stderr': res['stderr'],
            'execution_time_ms': res['execution_time_ms']
        }), 200

    testcases_dicts = [tc.to_dict(include_hidden=True) for tc in sample_cases]
    suite_res = execute_testcase_suite(source_code, language, testcases_dicts)

    return jsonify({
        'mode': 'sample_suite',
        'all_passed': suite_res['all_passed'],
        'passed_count': suite_res['passed_count'],
        'total_count': suite_res['total_count'],
        'overall_status': suite_res['overall_status'],
        'results': suite_res['results']
    }), 200


@assessment_bp.route('/code/submit', methods=['POST'])
@assessment_session_required
def submit_code():
    """Evaluate code against ALL testcases (hidden + sample) and save score."""
    submission_id = session.get('submission_id')
    submission = db.session.get(Submission, submission_id)
    if not submission or submission.status != 'in_progress':
        return api_error('Assessment session expired or inactive.', 403)

    data = request.get_json(silent=True) or {}
    problem_id = data.get('problem_id')
    language = (data.get('language') or 'python').strip()
    source_code = data.get('source_code') or ''

    if not problem_id or not source_code:
        return api_error('Problem ID and source code are required.', 400)

    problem = db.session.get(CodingProblem, problem_id)
    if not problem:
        return api_error('Problem not found.', 404)

    all_testcases = CodingTestCase.query.filter_by(problem_id=problem_id).order_by(
        CodingTestCase.is_hidden.asc(), CodingTestCase.id.asc()
    ).all()

    if not all_testcases:
        return api_error('No testcases configured for this problem.', 400)

    testcases_dicts = [tc.to_dict(include_hidden=True) for tc in all_testcases]
    suite_res = execute_testcase_suite(source_code, language, testcases_dicts)

    # Upsert CodingSubmission
    coding_sub = CodingSubmission.query.filter_by(
        submission_id=submission_id,
        problem_id=problem_id
    ).first()

    if not coding_sub:
        coding_sub = CodingSubmission(
            submission_id=submission_id,
            problem_id=problem_id,
            language=language,
            source_code=source_code,
            passed_testcases=suite_res['passed_count'],
            total_testcases=suite_res['total_count'],
            score=suite_res['total_score'],
            execution_time_ms=max((r['execution_time_ms'] for r in suite_res['results']), default=0),
            status=suite_res['overall_status'],
            submitted_at=datetime.utcnow()
        )
        db.session.add(coding_sub)
    else:
        coding_sub.language = language
        coding_sub.source_code = source_code
        coding_sub.passed_testcases = suite_res['passed_count']
        coding_sub.total_testcases = suite_res['total_count']
        coding_sub.score = suite_res['total_score']
        coding_sub.execution_time_ms = max((r['execution_time_ms'] for r in suite_res['results']), default=0)
        coding_sub.status = suite_res['overall_status']
        coding_sub.submitted_at = datetime.utcnow()

    # Update Submission total coding score
    db.session.flush()
    total_coding_pts = db.session.query(func.coalesce(func.sum(CodingSubmission.score), 0)).filter_by(
        submission_id=submission_id
    ).scalar() or 0
    submission.coding_score = total_coding_pts

    db.session.commit()

    return jsonify({
        'message': 'Code submitted successfully.',
        'all_passed': suite_res['all_passed'],
        'passed_count': suite_res['passed_count'],
        'total_count': suite_res['total_count'],
        'score': suite_res['total_score'],
        'max_score': suite_res['max_score'],
        'overall_status': suite_res['overall_status'],
        'results': suite_res['results']
    }), 200


@assessment_bp.route('/record-violation', methods=['POST'])
@assessment_session_required
def record_violation():
    submission_id = session['submission_id']
    submission = db.session.get(Submission, submission_id)

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
    
    # 1 single SQL query with joinedload for submission + assessment + answers
    submission = (
        db.session.query(Submission)
        .options(
            joinedload(Submission.assessment),
            joinedload(Submission.answers)
        )
        .filter(Submission.id == submission_id)
        .first()
    )

    if not submission:
        flash('Submission not found.', 'danger')
        return redirect(url_for('candidate.dashboard'))

    # Security check: candidate in session MUST match submission candidate
    if submission.candidate_id != session.get('candidate_id'):
        session.clear()
        flash('Session mismatch detected. Please register or log in again.', 'danger')
        return redirect(url_for('candidate.register'))

    if submission.status != 'in_progress':
        # Already submitted
        return redirect(url_for('assessment.result', submission_id=submission.id))

    # Fetch cached questions for this assessment
    questions = _get_cached_questions(submission.assessment_id)

    answer_map = {a.question_id: a.selected_option for a in submission.answers}
    correct = sum(
        1 for q in questions
        if answer_map.get(q.id) == q.correct_answer
    )
    total = len(questions)
    percentage = (correct / total * 100) if total > 0 else 0
    pass_pct = submission.assessment.pass_percentage if submission.assessment else 25.0
    status = 'pass' if percentage >= pass_pct else 'fail'

    # Sum coding score from coding submissions
    total_coding_pts = db.session.query(func.coalesce(func.sum(CodingSubmission.score), 0)).filter_by(
        submission_id=submission.id
    ).scalar() or 0
    submission.coding_score = total_coding_pts

    # Total score and combined percentage
    # (assuming 15 MCQs = 150 pts + 2 Coding Problems = 200 pts => 350 pts total)
    max_pts = (total * 10) + 200 if total > 0 else 350
    earned_pts = (correct * 10) + total_coding_pts
    percentage = (earned_pts / max_pts * 100) if max_pts > 0 else 0

    submission.score = correct
    submission.total_questions = total
    submission.percentage = percentage
    submission.status = status
    submission.submitted_at = datetime.utcnow()
    db.session.commit()

    # Clear assessment session keys
    session.pop('submission_id', None)
    session.pop('assessment_id', None)

    return redirect(url_for('assessment.result', submission_id=submission.id))


# ─────────────────────────────────────────────
# RESULT PAGE
# ─────────────────────────────────────────────

@assessment_bp.route('/result/<int:submission_id>')
def result(submission_id):
    submission = (
        db.session.query(Submission)
        .options(
            joinedload(Submission.candidate),
            joinedload(Submission.assessment),
            joinedload(Submission.answers)
        )
        .filter(Submission.id == submission_id)
        .first_or_404()
    )

    # Security: only the owning candidate (or admin) can view
    candidate_id_in_session = session.get('candidate_id')
    if candidate_id_in_session != submission.candidate_id:
        from flask_login import current_user
        if not current_user.is_authenticated:
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('candidate.register'))

    questions = _get_cached_questions(submission.assessment_id)
    answers = {a.question_id: a.selected_option for a in submission.answers}

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
