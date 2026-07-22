"""
ElevateIQ — Admin Blueprint
Handles: login/logout, dashboard, assessment CRUD,
         question CRUD, results viewing, and export.
"""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from models.models import db, Admin, Assessment, Question, Submission, Candidate
from services.stats_service import get_dashboard_stats, get_recent_results
from services.export_service import export_csv, export_xlsx
from utils.helpers import sanitize_string, api_success, api_error, paginate_query

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('admin/login.html')

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=False)
            next_page = request.args.get('next')
            flash(f'Welcome back, {admin.email}!', 'success')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    stats = get_dashboard_stats()
    
    # Retrieve passed and failed members separately using joinedload to avoid N+1
    passed_results = (
        db.session.query(Submission)
        .options(joinedload(Submission.candidate))
        .filter_by(status='pass')
        .order_by(Submission.submitted_at.desc())
        .limit(10)
        .all()
    )
    failed_results = (
        db.session.query(Submission)
        .options(joinedload(Submission.candidate))
        .filter_by(status='fail')
        .order_by(Submission.submitted_at.desc())
        .limit(10)
        .all()
    )
    
    # Only load the 10 most recent assessments for the dashboard sidebar
    assessments = Assessment.query.order_by(Assessment.created_at.desc()).limit(10).all()
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        passed_results=passed_results,
        failed_results=failed_results,
        assessments=assessments
    )


# ─────────────────────────────────────────────
# ASSESSMENT MANAGEMENT
# ─────────────────────────────────────────────

@admin_bp.route('/assessments')
@login_required
def assessments():
    all_assessments = Assessment.query.order_by(Assessment.created_at.desc()).all()
    return render_template('admin/assessments.html', assessments=all_assessments)


@admin_bp.route('/assessments/create', methods=['POST'])
@login_required
def create_assessment():
    title = sanitize_string(request.form.get('title', ''))
    description = sanitize_string(request.form.get('description', ''), max_length=1000)
    duration = request.form.get('duration', '60')
    pass_pct = request.form.get('pass_percentage', '60')

    if not title:
        flash('Assessment title is required.', 'danger')
        return redirect(url_for('admin.assessments'))

    try:
        duration = int(duration)
        pass_pct = float(pass_pct)
        if duration < 1 or pass_pct < 0 or pass_pct > 100:
            raise ValueError
    except ValueError:
        flash('Invalid duration or pass percentage.', 'danger')
        return redirect(url_for('admin.assessments'))

    assessment = Assessment(
        title=title,
        description=description,
        duration=duration,
        pass_percentage=pass_pct,
        status='inactive'
    )
    db.session.add(assessment)
    db.session.commit()
    flash(f'Assessment "{title}" created successfully.', 'success')
    return redirect(url_for('admin.assessments'))


@admin_bp.route('/assessments/<int:assessment_id>/edit', methods=['POST'])
@login_required
def edit_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    assessment.title = sanitize_string(request.form.get('title', assessment.title))
    assessment.description = sanitize_string(
        request.form.get('description', assessment.description or ''), max_length=1000
    )
    try:
        assessment.duration = int(request.form.get('duration', assessment.duration))
        assessment.pass_percentage = float(
            request.form.get('pass_percentage', assessment.pass_percentage)
        )
    except ValueError:
        flash('Invalid duration or pass percentage.', 'danger')
        return redirect(url_for('admin.assessments'))

    db.session.commit()
    flash('Assessment updated successfully.', 'success')
    return redirect(url_for('admin.assessments'))


@admin_bp.route('/assessments/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    title = assessment.title
    db.session.delete(assessment)
    db.session.commit()
    flash(f'Assessment "{title}" deleted.', 'success')
    return redirect(url_for('admin.assessments'))


@admin_bp.route('/assessments/<int:assessment_id>/toggle-status', methods=['POST'])
@login_required
def toggle_assessment_status(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)

    if assessment.status == 'inactive':
        assessment.status = 'active'
        msg = f'Assessment "{assessment.title}" is now ACTIVE.'
    else:
        assessment.status = 'inactive'
        msg = f'Assessment "{assessment.title}" deactivated.'

    db.session.commit()
    flash(msg, 'success')
    return redirect(url_for('admin.assessments'))


# ─────────────────────────────────────────────
# QUESTION BANK MANAGEMENT
# ─────────────────────────────────────────────

@admin_bp.route('/assessments/<int:assessment_id>/questions')
@login_required
def questions(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q_query = Question.query.filter_by(assessment_id=assessment_id).order_by(Question.id)
    pagination = q_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'admin/questions.html',
        assessment=assessment,
        questions=pagination.items,
        pagination=pagination,
    )


@admin_bp.route('/assessments/<int:assessment_id>/questions/add', methods=['POST'])
@login_required
def add_question(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    question_text = request.form.get('question', '').strip()
    option_a = request.form.get('option_a', '').strip()
    option_b = request.form.get('option_b', '').strip()
    option_c = request.form.get('option_c', '').strip()
    option_d = request.form.get('option_d', '').strip()
    correct_answer = request.form.get('correct_answer', '').strip().upper()

    if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.questions', assessment_id=assessment_id))

    if correct_answer not in ('A', 'B', 'C', 'D'):
        flash('Correct answer must be A, B, C, or D.', 'danger')
        return redirect(url_for('admin.questions', assessment_id=assessment_id))

    q = Question(
        assessment_id=assessment_id,
        question=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct_answer,
    )
    db.session.add(q)
    db.session.commit()
    flash('Question added successfully.', 'success')
    return redirect(url_for('admin.questions', assessment_id=assessment_id))


@admin_bp.route('/questions/<int:question_id>/edit', methods=['POST'])
@login_required
def edit_question(question_id):
    q = Question.query.get_or_404(question_id)
    q.question = request.form.get('question', q.question).strip()
    q.option_a = request.form.get('option_a', q.option_a).strip()
    q.option_b = request.form.get('option_b', q.option_b).strip()
    q.option_c = request.form.get('option_c', q.option_c).strip()
    q.option_d = request.form.get('option_d', q.option_d).strip()
    correct = request.form.get('correct_answer', q.correct_answer).strip().upper()
    if correct in ('A', 'B', 'C', 'D'):
        q.correct_answer = correct
    db.session.commit()
    flash('Question updated.', 'success')
    return redirect(url_for('admin.questions', assessment_id=q.assessment_id))


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    q = Question.query.get_or_404(question_id)
    assessment_id = q.assessment_id
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin.questions', assessment_id=assessment_id))


# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────

@admin_bp.route('/results')
@login_required
def results():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all').strip().lower()
    per_page = 20

    from sqlalchemy.orm import joinedload
    query = (
        db.session.query(Submission)
        .options(
            joinedload(Submission.candidate),
            joinedload(Submission.assessment)
        )
        .filter(Submission.status != 'in_progress')
    )

    if status in ('pass', 'fail'):
        query = query.filter(Submission.status == status)

    query = query.order_by(Submission.submitted_at.desc())

    if search:
        from models.models import Candidate as Cand
        like = f'%{search}%'
        query = query.join(Submission.candidate).filter(
            db.or_(
                Cand.full_name.ilike(like),
                Cand.hall_ticket.ilike(like),
                Cand.email.ilike(like),
            )
        )

    total = query.count()
    submissions = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        'admin/results.html',
        submissions=submissions,
        page=page,
        total_pages=total_pages,
        total=total,
        search=search,
        status=status,
        per_page=per_page,
    )


@admin_bp.route('/results/export')
@login_required
def export_results():
    fmt = request.args.get('fmt', 'csv').lower()
    search = request.args.get('search', '').strip()
    status = request.args.get('status', None)
    assessment_id = request.args.get('assessment_id', None, type=int)

    if fmt == 'xlsx':
        return export_xlsx(search=search, assessment_id=assessment_id, status=status)
    return export_csv(search=search, assessment_id=assessment_id, status=status)


# ─────────────────────────────────────────────
# API — Assessment data (JSON) for modals
# ─────────────────────────────────────────────

@admin_bp.route('/api/assessments/<int:assessment_id>')
@login_required
def api_assessment(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    return jsonify(assessment.to_dict())


@admin_bp.route('/api/questions/<int:question_id>')
@login_required
def api_question(question_id):
    q = Question.query.get_or_404(question_id)
    return jsonify(q.to_dict(include_answer=True))
