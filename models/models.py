"""
ElevateIQ — SQLAlchemy ORM Models
All database tables with proper indexes, relationships, and constraints.
"""
from datetime import datetime
from sqlalchemy import func, select
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────
# Admin Model
# ─────────────────────────────────────────────
class Admin(db.Model, UserMixin):
    __tablename__ = 'assessment_admins'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.email}>'


# ─────────────────────────────────────────────
# Candidate Model
# ─────────────────────────────────────────────
class Candidate(db.Model):
    __tablename__ = 'assessment_candidates'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    hall_ticket = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submissions = db.relationship(
        'Submission', backref='candidate', lazy='select',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'hall_ticket': self.hall_ticket,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Candidate {self.hall_ticket}>'


# ─────────────────────────────────────────────
# Assessment Model
# ─────────────────────────────────────────────
class Assessment(db.Model):
    __tablename__ = 'assessment_drives'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Integer, nullable=False)          # minutes
    pass_percentage = db.Column(db.Float, nullable=False, default=25.0)
    status = db.Column(db.String(20), nullable=False, default='inactive')  # active | inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships — use lazy='select' so SQLAlchemy can batch-load with joinedload
    questions = db.relationship(
        'Question', backref='assessment', lazy='select',
        cascade='all, delete-orphan', order_by='Question.id'
    )
    submissions = db.relationship(
        'Submission', backref='assessment', lazy='select'
    )

    @property
    def question_count(self):
        """Return annotated count if available (from joinedload/subquery),
        otherwise fall back to a single COUNT query."""
        # If the query annotated _question_count, use it (zero SQL)
        annotated = getattr(self, '_question_count', None)
        if annotated is not None:
            return annotated
        # Fallback: single query (only used in .to_dict() edge cases)
        return db.session.query(func.count(Question.id)).filter(
            Question.assessment_id == self.id
        ).scalar() or 0

    @property
    def is_active(self):
        return self.status == 'active'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'pass_percentage': self.pass_percentage,
            'status': self.status,
            'question_count': self.question_count,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Assessment {self.title}>'


# ─────────────────────────────────────────────
# Question Model
# ─────────────────────────────────────────────
class Question(db.Model):
    __tablename__ = 'assessment_questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey('assessment_drives.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # A | B | C | D

    # Relationships
    answers = db.relationship(
        'Answer', backref='question', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_answer=False):
        import re
        clean_q = re.sub(r'^Q\d+[\.\:\s]+\s*', '', self.question or '', flags=re.IGNORECASE)
        data = {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question': clean_q,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'option_c': self.option_c,
            'option_d': self.option_d,
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
        return data

    def __repr__(self):
        return f'<Question {self.id}>'


# ─────────────────────────────────────────────
# Submission Model
# ─────────────────────────────────────────────
class Submission(db.Model):
    __tablename__ = 'assessment_submissions'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey('assessment_candidates.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    assessment_id = db.Column(
        db.Integer, db.ForeignKey('assessment_drives.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    score = db.Column(db.Integer, default=0)
    coding_score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    violations = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in_progress', index=True)  # in_progress | pass | fail
    submitted_at = db.Column(db.DateTime, nullable=True, index=True)

    # Relationships
    coding_submissions = db.relationship('CodingSubmission', backref='submission', cascade='all, delete-orphan', lazy='select')
    # Relationships — lazy='select' allows joinedload() in route queries
    answers = db.relationship(
        'Answer', backref='submission', lazy='select',
        cascade='all, delete-orphan'
    )

    # Prevent duplicate submissions per candidate per assessment & index query paths
    __table_args__ = (
        db.UniqueConstraint('candidate_id', 'assessment_id', name='uq_assessment_candidate_drive'),
        db.Index('ix_submissions_status_submitted', 'status', 'submitted_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_name': self.candidate.full_name if self.candidate else '',
            'candidate_email': self.candidate.email if self.candidate else '',
            'hall_ticket': self.candidate.hall_ticket if self.candidate else '',
            'assessment_title': self.assessment.title if self.assessment else '',
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round(self.percentage, 2),
            'violations': self.violations,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        }

    def __repr__(self):
        return f'<Submission {self.id} — {self.status}>'

    @property
    def submitted_at_ist(self):
        if not self.submitted_at:
            return None
        from datetime import timedelta
        return self.submitted_at + timedelta(hours=5, minutes=30)


# ─────────────────────────────────────────────
# Answer Model
# ─────────────────────────────────────────────
class Answer(db.Model):
    __tablename__ = 'assessment_answers'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('assessment_submissions.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey('assessment_questions.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    selected_option = db.Column(db.String(1), nullable=True)  # A | B | C | D | None

    # Each question can only have one answer per submission
    __table_args__ = (
        db.UniqueConstraint('submission_id', 'question_id', name='uq_assessment_submission_question'),
        # Composite index for fast answer lookups during auto-save + submission scoring
        db.Index('ix_answers_submission_question', 'submission_id', 'question_id'),
    )

    def __repr__(self):
        return f'<Answer sub={self.submission_id} q={self.question_id} opt={self.selected_option}>'


# ─────────────────────────────────────────────
# Coding Challenge Model
# ─────────────────────────────────────────────
class CodingProblem(db.Model):
    __tablename__ = 'assessment_coding_problems'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey('assessment_drives.id', ondelete='CASCADE'),
        nullable=True, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    difficulty = db.Column(db.String(20), default='Medium')
    points = db.Column(db.Integer, default=100)
    problem_statement = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text, nullable=True)
    output_format = db.Column(db.Text, nullable=True)
    constraints = db.Column(db.Text, nullable=True)
    time_limit_seconds = db.Column(db.Integer, default=5)
    memory_limit_mb = db.Column(db.Integer, default=256)
    starter_code_json = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    testcases = db.relationship(
        'CodingTestCase', backref='problem', cascade='all, delete-orphan',
        lazy='select', order_by='CodingTestCase.id'
    )
    submissions = db.relationship(
        'CodingSubmission', backref='problem', cascade='all, delete-orphan',
        lazy='select'
    )

    def to_dict(self, include_testcases=False):
        data = {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'title': self.title,
            'difficulty': self.difficulty,
            'points': self.points,
            'problem_statement': self.problem_statement,
            'input_format': self.input_format,
            'output_format': self.output_format,
            'constraints': self.constraints,
            'time_limit_seconds': self.time_limit_seconds,
            'memory_limit_mb': self.memory_limit_mb,
            'starter_code_json': self.starter_code_json or {},
            'sample_testcases': [tc.to_dict() for tc in self.testcases if not tc.is_hidden],
        }
        if include_testcases:
            data['testcases'] = [tc.to_dict(include_hidden=True) for tc in self.testcases]
        return data

    def __repr__(self):
        return f'<CodingProblem {self.title}>'


# ─────────────────────────────────────────────
# Coding Test Case Model
# ─────────────────────────────────────────────
class CodingTestCase(db.Model):
    __tablename__ = 'assessment_coding_testcases'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(
        db.Integer, db.ForeignKey('assessment_coding_problems.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=True)
    weight = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self, include_hidden=False):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'input_data': self.input_data if (not self.is_hidden or include_hidden) else 'Hidden',
            'expected_output': self.expected_output if (not self.is_hidden or include_hidden) else 'Hidden',
            'is_hidden': self.is_hidden,
            'weight': self.weight
        }

    def __repr__(self):
        return f'<CodingTestCase prob={self.problem_id} hidden={self.is_hidden}>'


# ─────────────────────────────────────────────
# Coding Submission Model
# ─────────────────────────────────────────────
class CodingSubmission(db.Model):
    __tablename__ = 'assessment_coding_submissions'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('assessment_submissions.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    problem_id = db.Column(
        db.Integer, db.ForeignKey('assessment_coding_problems.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    language = db.Column(db.String(30), nullable=False) # python, javascript, java, cpp
    source_code = db.Column(db.Text, nullable=False)
    passed_testcases = db.Column(db.Integer, default=0)
    total_testcases = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    execution_time_ms = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='Submitted') # Accepted, Wrong Answer, Time Limit Exceeded, Runtime Error, Compilation Error
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('submission_id', 'problem_id', name='uq_coding_submission_problem'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'language': self.language,
            'source_code': self.source_code,
            'passed_testcases': self.passed_testcases,
            'total_testcases': self.total_testcases,
            'score': self.score,
            'execution_time_ms': self.execution_time_ms,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

    def __repr__(self):
        return f'<CodingSubmission sub={self.submission_id} prob={self.problem_id} score={self.score}>'
