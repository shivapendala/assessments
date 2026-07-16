# ElevateIQ — Campus Recruitment Assessment Portal

A production-ready online assessment platform for conducting MCQ-based campus recruitment drives.

**Stack:** Flask · Neon PostgreSQL · SQLAlchemy · Gunicorn · Nginx

---

## Features

- 🔐 Secure Admin Portal (Flask-Login + bcrypt)
- 📝 Assessment & Question Bank Management (CRUD)
- 👤 Candidate Self-Registration
- ⚙️ Full Assessment Engine with countdown timer
- 🛡️ Anti-Cheat: tab-switch detection (auto-submit on 3 violations)
- 💾 Auto-save answers (server + localStorage)
- 📊 Results Dashboard with search & pagination
- 📥 Export to CSV & XLSX
- 🌐 Production-ready with Gunicorn + Nginx

---

## Local Development Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd "elevateiq recruitment"
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

Key variables:
```env
SECRET_KEY=your-32-char-random-secret
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/elevateiq?sslmode=require
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=SecurePassword123!
FLASK_ENV=development
```

### 4. Initialize the database

```bash
# Create tables
flask init-db

# Create default admin
flask create-admin
```

Or run the standalone script:
```bash
python create_admin.py
```

### 5. Run development server

```bash
flask run
# or
python app.py
```

Visit: http://localhost:5000

---

## Production Deployment (Hostinger VPS / Ubuntu)

### 1. Server prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

### 2. Upload project

```bash
scp -r "elevateiq recruitment/" user@your-server:/var/www/elevateiq/
```

### 3. Virtual environment on server

```bash
cd /var/www/elevateiq
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure .env

```bash
cp .env.example .env
nano .env   # fill in DATABASE_URL, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
```

### 5. Initialize DB and create admin

```bash
source venv/bin/activate
export FLASK_APP=app.py
flask init-db
flask create-admin
```

### 6. Systemd service

Create `/etc/systemd/system/elevateiq.service`:

```ini
[Unit]
Description=ElevateIQ Assessment Portal
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/elevateiq
EnvironmentFile=/var/www/elevateiq/.env
ExecStart=/var/www/elevateiq/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable elevateiq
sudo systemctl start elevateiq
sudo systemctl status elevateiq
```

### 7. Nginx configuration

```bash
sudo cp nginx.conf /etc/nginx/sites-available/elevateiq
# Edit server_name with your actual domain
sudo nano /etc/nginx/sites-available/elevateiq

sudo ln -s /etc/nginx/sites-available/elevateiq /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## Admin Workflow

1. Login at `/admin/login`
2. Create an Assessment (title, duration, pass %)
3. Add questions to the assessment
4. Activate the assessment (only one can be active at a time)
5. Candidates can now register and take the assessment
6. View results at `/admin/results`
7. Export as CSV or XLSX

---

## Candidate Workflow

1. Register at `/register` (name, email, hall ticket)
2. Dashboard shows the active assessment + instructions
3. Click "Start Assessment" (one-time only)
4. Answer MCQs with timer running
5. Submit — result shown immediately

---

## Database Schema

| Table       | Purpose |
|-------------|---------|
| admins      | Admin accounts |
| candidates  | Registered candidates |
| assessments | Assessment definitions |
| questions   | MCQ questions per assessment |
| submissions | Candidate attempt records |
| answers     | Per-question answers for each submission |

---

## Security Notes

- Passwords hashed with Werkzeug (bcrypt)
- CSRF protection on all forms (Flask-WTF)
- SQLAlchemy ORM (no raw SQL → no injection)
- Session cookies: HttpOnly, SameSite=Lax, Secure (production)
- Environment variables for all secrets
- One-attempt enforcement at server level

---

## Performance Notes

- SQLAlchemy connection pool: `pool_size=10, max_overflow=20`
- Indexed columns: `candidates.email`, `candidates.hall_ticket`, `questions.assessment_id`, `submissions.candidate_id`
- Paginated results (20 per page)
- Gevent async workers in Gunicorn (100+ concurrent candidates)
- Questions loaded once per assessment session

---

## Project Structure

```
elevateiq recruitment/
├── app.py                  # Application factory
├── config.py               # Dev/Prod/Test config
├── create_admin.py         # Admin seed script
├── requirements.txt
├── .env.example
├── gunicorn.conf.py
├── nginx.conf
├── models/
│   └── models.py           # SQLAlchemy ORM
├── routes/
│   ├── admin.py            # Admin blueprint
│   ├── candidate.py        # Candidate blueprint
│   └── assessment.py       # Assessment engine blueprint
├── services/
│   ├── export_service.py   # CSV/XLSX export
│   └── stats_service.py    # Dashboard stats
├── utils/
│   └── helpers.py          # Validators, decorators
├── static/
│   ├── css/main.css        # Complete design system
│   └── js/
│       ├── admin.js        # Admin UI interactions
│       ├── assessment.js   # Timer, anti-cheat, nav
│       └── results.js      # Search, sort
└── templates/
    ├── base.html
    ├── admin/              # Admin templates
    └── candidate/          # Candidate templates
```

---

## Support

For issues, contact the development team or raise an issue in the project repository.

**ElevateIQ** · Campus Recruitment Assessment Platform
