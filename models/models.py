"""
ElevateIQ — SQLAlchemy ORM Models
All database tables with proper indexes, relationships, and constraints.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────
# Admin Model
# ─────────────────────────────────────────────
class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'

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
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    hall_ticket = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submissions = db.relationship(
        'Submission', backref='candidate', lazy='dynamic',
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
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Integer, nullable=False)          # minutes
    pass_percentage = db.Column(db.Float, nullable=False, default=60.0)
    status = db.Column(db.String(20), nullable=False, default='inactive')  # active | inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questions = db.relationship(
        'Question', backref='assessment', lazy='dynamic',
        cascade='all, delete-orphan', order_by='Question.id'
    )
    submissions = db.relationship(
        'Submission', backref='assessment', lazy='dynamic'
    )

    @property
    def question_count(self):
        return self.questions.count()

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
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey('assessments.id', ondelete='CASCADE'),
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
        data = {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question': self.question,
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
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    assessment_id = db.Column(
        db.Integer, db.ForeignKey('assessments.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    violations = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in_progress', index=True)  # in_progress | pass | fail
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    answers = db.relationship(
        'Answer', backref='submission', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Prevent duplicate submissions per candidate per assessment
    __table_args__ = (
        db.UniqueConstraint('candidate_id', 'assessment_id', name='uq_candidate_assessment'),
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
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('submissions.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    selected_option = db.Column(db.String(1), nullable=True)  # A | B | C | D | None

    # Each question can only have one answer per submission
    __table_args__ = (
        db.UniqueConstraint('submission_id', 'question_id', name='uq_submission_question'),
    )

    def __repr__(self):
        return f'<Answer sub={self.submission_id} q={self.question_id} opt={self.selected_option}>'
