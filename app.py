"""
ElevateIQ — Application Factory
Flask app creation with all extensions and blueprints registered.
"""
import os
from datetime import timedelta
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from config import get_config
from models.models import db, Admin
from extensions import cache


# ─── Extension instances ───────────────────────────────────────────────────
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
# cache is imported from extensions.py to avoid circular imports


def create_app(config_class=None):
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Static file browser caching (1 year in production, 0 in debug)
    is_prod = not app.config.get('DEBUG', False)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(days=365) if is_prod else timedelta(seconds=0)

    # Flask-Caching: SimpleCache (in-process, no Redis needed)
    app.config.setdefault('CACHE_TYPE', 'SimpleCache')
    app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)  # 5 minutes

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cache.init_app(app)

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
        return db.session.get(Admin, int(user_id))

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

    # ── DB Connection Warmup (eliminates cold start on first requests) ─────
    _warmed_up = {'done': False}

    @app.before_request
    def warmup_db():
        if _warmed_up['done']:
            return
        _warmed_up['done'] = True
        try:
            # Pre-establish DB connections and prime caches
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
            # Prime the active assessments cache
            from routes.candidate import _get_active_assessments
            _get_active_assessments()
        except Exception:
            pass

    # ── Context processors ─────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {'app_name': 'ElevateIQ'}

    @app.cli.command('init-db')
    def init_db():
        """Create all database tables, seed default admin and assessment drives."""
        with app.app_context():
            db.create_all()
            _create_default_admin(app)
            try:
                from seed_jd_assessment import seed_assessment as seed_it
                from seed_non_it_assessment import seed_assessment as seed_non_it
                seed_it()
                seed_non_it()
            except Exception as e:
                print(f"Seeding notice: {e}")
            print('OK - Database initialized, admin created, and assessments seeded!')

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
