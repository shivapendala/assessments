"""
ElevateIQ — Application Factory
Flask app creation with all extensions and blueprints registered.
"""
import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from config import get_config
from models.models import db, Admin


# ─── Extension instances ───────────────────────────────────────────────────
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_class=None):
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    # ── CSRF: allow JSON API calls with X-CSRFToken header ─────────────────
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken']

    # ── Blueprints ─────────────────────────────────────────────────────────
    from routes.admin import admin_bp
    from routes.candidate import candidate_bp
    from routes.assessment import assessment_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(assessment_bp)

    # ── User loader for Flask-Login ─────────────────────────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    # ── Error handlers ─────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Health check ───────────────────────────────────────────────────────
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'ElevateIQ'}, 200

    # ── Context processors ─────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {'app_name': 'ElevateIQ'}

    # ── CLI Commands ───────────────────────────────────────────────────────
    @app.cli.command('init-db')
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            print('OK - Database tables created.')

    @app.cli.command('create-admin')
    def create_admin_cmd():
        """Create the default admin from environment variables."""
        _create_default_admin(app)

    return app


def _create_default_admin(app):
    """Seed the default admin account."""
    with app.app_context():
        email = os.environ.get('ADMIN_EMAIL', 'admin@elevateiq.com')
        password = os.environ.get('ADMIN_PASSWORD', 'Admin@2024!')

        existing = Admin.query.filter_by(email=email).first()
        if existing:
            print(f'Admin already exists: {email}')
            return

        admin = Admin(email=email)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'OK - Admin created: {email}')


# ─── Entry point ──────────────────────────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=5000)
