import os
from models.models import db
from app import create_app

app = create_app()
with app.app_context():
    print("Dropping all assessment tables...")
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_answers CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_submissions CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_questions CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_drives CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_candidates CASCADE;"))
    db.session.execute(db.text("DROP TABLE IF EXISTS assessment_admins CASCADE;"))
    db.session.commit()
    print("All assessment tables dropped successfully!")

    print("Re-creating all assessment tables...")
    db.create_all()
    print("All assessment tables created successfully!")
