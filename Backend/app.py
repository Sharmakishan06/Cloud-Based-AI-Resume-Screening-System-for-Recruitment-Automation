"""
Cloud-Based AI Resume Screening System
Student: Kishan Kumar Sharma | Enrollment: O24MCA110066
Degree: MCA | Mentor: Hari Krishna
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from ai_engine import ResumeScreeningEngine
from resume_parser import ResumeParser

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'screening.db')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

# Initialize AI Engine
engine = ResumeScreeningEngine()
parser = ResumeParser()


# ─────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT,
            experience_years INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            filename TEXT,
            extracted_text TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            match_score REAL DEFAULT 0.0,
            rank_position INTEGER DEFAULT 0,
            shortlisted INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
    """)

    # Seed sample job if empty
    cur.execute("SELECT COUNT(*) FROM jobs")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO jobs (title, description, required_skills, experience_years)
            VALUES (?, ?, ?, ?)
        """, (
            "Python Backend Developer",
            "We are looking for an experienced Python developer with strong knowledge of Flask, REST APIs, databases, and cloud services. The candidate should have experience in AI/ML integration and be comfortable working with AWS or GCP.",
            json.dumps(["Python", "Flask", "REST API", "SQL", "AWS", "Docker", "Machine Learning", "Git"]),
            2
        ))
        cur.execute("""
            INSERT INTO jobs (title, description, required_skills, experience_years)
            VALUES (?, ?, ?, ?)
        """, (
            "Data Science Intern",
            "Looking for a data science intern with Python and machine learning skills. Experience with pandas, numpy, scikit-learn preferred. Strong analytical skills required.",
            json.dumps(["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "Statistics", "Data Analysis"]),
            0
        ))

    conn.commit()
    conn.close()


init_db()


# ─────────────────────────────────────────
# Utility
# ─────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────
# Routes – Serve Frontend
# ─────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    full_path = os.path.join(app.static_folder, path)
    if os.path.isfile(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ─────────────────────────────────────────
# API – Jobs
# ─────────────────────────────────────────

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    conn = get_db()
    jobs = conn.execute(
        "SELECT id, title, description, required_skills, experience_years, created_at FROM jobs ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(j) for j in jobs])


@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('description'):
        return jsonify({'error': 'Title and description are required'}), 400

    skills = data.get('skills', [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',') if s.strip()]

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO jobs (title, description, required_skills, experience_years) VALUES (?, ?, ?, ?)",
        (data['title'], data['description'], json.dumps(skills), int(data.get('experience_years', 0)))
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': job_id, 'message': 'Job created successfully'}), 201


@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(dict(job))


@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    conn = get_db()
    conn.execute("DELETE FROM candidates WHERE job_id = ?", (job_id,))
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Job and associated candidates deleted'})


# ─────────────────────────────────────────
# API – Resumes
# ─────────────────────────────────────────

@app.route('/api/jobs/<int:job_id>/upload', methods=['POST'])
def upload_resumes(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404

    job_data = dict(job)
    conn.close()

    if 'resumes' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('resumes')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files selected'}), 400

    required_skills = json.loads(job_data['required_skills'] or '[]')
    job_description = job_data['description']

    results = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Parse resume
            parsed = parser.parse(filepath)
            extracted_text = parsed.get('text', '')
            candidate_name = parsed.get('name', filename.rsplit('.', 1)[0].replace('_', ' ').title())
            email = parsed.get('email', '')
            phone = parsed.get('phone', '')
            skills_found = parsed.get('skills', [])
            education = parsed.get('education', '')
            experience_text = parsed.get('experience', '')

            # AI Scoring
            score = engine.calculate_match_score(
                resume_text=extracted_text,
                job_description=job_description,
                required_skills=required_skills,
                candidate_skills=skills_found
            )

            conn = get_db()
            cur = conn.execute("""
                INSERT INTO candidates
                (job_id, name, email, phone, filename, extracted_text, skills, experience, education, match_score, shortlisted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, candidate_name, email, phone, unique_filename,
                extracted_text[:5000],
                json.dumps(skills_found),
                experience_text[:1000],
                education[:500],
                round(score * 100, 2),
                1 if score >= 0.6 else 0
            ))
            candidate_id = cur.lastrowid
            conn.commit()
            conn.close()

            results.append({
                'id': candidate_id,
                'name': candidate_name,
                'filename': filename,
                'match_score': round(score * 100, 2),
                'skills': skills_found,
                'shortlisted': score >= 0.6
            })

    # Update ranks
    _update_ranks(job_id)

    return jsonify({
        'message': f'{len(results)} resume(s) processed successfully',
        'candidates': results
    })


def _update_ranks(job_id):
    conn = get_db()
    candidates = conn.execute(
        "SELECT id FROM candidates WHERE job_id = ? ORDER BY match_score DESC",
        (job_id,)
    ).fetchall()
    for rank, c in enumerate(candidates, 1):
        conn.execute("UPDATE candidates SET rank_position = ? WHERE id = ?", (rank, c['id']))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# API – Candidates
# ─────────────────────────────────────────

@app.route('/api/jobs/<int:job_id>/candidates', methods=['GET'])
def get_candidates(job_id):
    shortlisted_only = request.args.get('shortlisted', 'false').lower() == 'true'
    conn = get_db()
    query = "SELECT * FROM candidates WHERE job_id = ?"
    params = [job_id]
    if shortlisted_only:
        query += " AND shortlisted = 1"
    query += " ORDER BY match_score DESC"
    candidates = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for c in candidates:
        d = dict(c)
        d['skills'] = json.loads(d.get('skills') or '[]')
        result.append(d)
    return jsonify(result)


@app.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    conn = get_db()
    c = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    if not c:
        return jsonify({'error': 'Candidate not found'}), 404
    d = dict(c)
    d['skills'] = json.loads(d.get('skills') or '[]')
    return jsonify(d)


@app.route('/api/candidates/<int:candidate_id>/shortlist', methods=['PUT'])
def toggle_shortlist(candidate_id):
    data = request.get_json()
    shortlisted = 1 if data.get('shortlisted') else 0
    conn = get_db()
    conn.execute("UPDATE candidates SET shortlisted = ? WHERE id = ?", (shortlisted, candidate_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated', 'shortlisted': bool(shortlisted)})


@app.route('/api/candidates/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    conn = get_db()
    c = conn.execute("SELECT filename FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    if c:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], c['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
    conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Candidate deleted'})


# ─────────────────────────────────────────
# API – Dashboard Stats
# ─────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    shortlisted = conn.execute("SELECT COUNT(*) FROM candidates WHERE shortlisted = 1").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(match_score) FROM candidates").fetchone()[0] or 0
    recent = conn.execute("""
        SELECT c.name, c.match_score, c.shortlisted, j.title as job_title
        FROM candidates c JOIN jobs j ON c.job_id = j.id
        ORDER BY c.created_at DESC LIMIT 5
    """).fetchall()
    conn.close()
    return jsonify({
        'total_jobs': total_jobs,
        'total_candidates': total_candidates,
        'shortlisted': shortlisted,
        'average_score': round(avg_score, 1),
        'recent_candidates': [dict(r) for r in recent]
    })


# ─────────────────────────────────────────
# API – Health
# ─────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'AI Resume Screening System is running'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

# ─────────────────────────────────────────
# API – Dataset / Seed (auto-loads Resume.csv)
# ─────────────────────────────────────────

@app.route('/api/seed', methods=['POST'])
def seed_dataset():
    """Seed the database from Resume.csv dataset."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'dataset', 'Resume.csv')
    if not os.path.exists(csv_path):
        return jsonify({'error': 'Dataset not found. Place Resume.csv in the dataset/ folder.'}), 404
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from seed_data import seed
        n = int(request.get_json(silent=True, force=True).get('per_category', 10)
                if request.data else 10)
        seed(csv_path, DATABASE, n)
        conn = get_db()
        stats = {
            'total_jobs':       conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
            'total_candidates': conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
            'shortlisted':      conn.execute("SELECT COUNT(*) FROM candidates WHERE shortlisted=1").fetchone()[0],
        }
        conn.close()
        return jsonify({'message': f'Dataset seeded successfully ({n} resumes per category)', **stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/categories', methods=['GET'])
def get_categories():
    """Return all distinct job categories available in the dataset."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'dataset', 'Resume.csv')
    if not os.path.exists(csv_path):
        return jsonify({'categories': [], 'total': 0})
    import csv as _csv
    from collections import Counter
    with open(csv_path, encoding='utf-8', errors='ignore') as f:
        rows = list(_csv.DictReader(f))
    cats = Counter(r['Category'].strip().upper() for r in rows)
    return jsonify({
        'categories': [{'name': k, 'count': v} for k, v in sorted(cats.items())],
        'total': len(rows)
    })
