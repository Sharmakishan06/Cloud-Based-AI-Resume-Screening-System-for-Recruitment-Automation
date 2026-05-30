# Cloud-Based AI Resume Screening System

**Student:** Kishan Kumar Sharma  
**Enrollment ID:** O24MCA110066  
**Degree:** MCA – Masters in Computer Applications  
**Mentor:** Hari Krishna  

---

## Project Overview

A cloud-hosted AI-powered web application that automates the resume screening and candidate shortlisting process for recruiters. The system uses TF-IDF vectorization and cosine similarity to rank resumes against job descriptions.

## Features

- Upload PDF / DOCX resumes in bulk
- AI-based resume parsing (name, email, phone, skills, education)
- TF-IDF + cosine similarity match scoring
- Automatic candidate ranking and shortlisting
- Recruiter dashboard with filters and analytics
- REST API backend (Flask)
- Cloud deployment on Render (free tier)

## Tech Stack

| Layer       | Technology                    |
|-------------|-------------------------------|
| Backend     | Python 3.11, Flask 3.0        |
| AI Engine   | TF-IDF (custom), Cosine Sim   |
| Parsing     | pdfplumber, python-docx       |
| Database    | SQLite                        |
| Frontend    | HTML5, CSS3, Vanilla JS       |
| Hosting     | Render.com (free)             |
| Version Ctrl| Git / GitHub                  |

---

## Local Setup

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/resume-screening-ai.git
cd resume-screening-ai

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run the app
cd backend
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Deploy to Render (FREE – No Credit Card Needed)

1. **Push to GitHub** (see GitHub Setup below)

2. Go to **https://render.com** → Sign up free with GitHub

3. Click **"New +"** → **"Web Service"**

4. Connect your GitHub repo

5. Set these settings:
   - **Name:** `resume-screening-ai`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

6. Click **"Create Web Service"**

7. Wait ~3 minutes → your app is LIVE! 🎉

Your URL will be: `https://resume-screening-ai.onrender.com`

---

## GitHub Setup

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: AI Resume Screening System"

# Create repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/resume-screening-ai.git
git branch -M main
git push -u origin main
```

---

## Project Structure

```
resume-screening-ai/
├── backend/
│   ├── app.py              # Flask application & API routes
│   ├── ai_engine.py        # TF-IDF AI matching engine
│   ├── resume_parser.py    # PDF/DOCX resume parser
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Recruiter dashboard
│   └── assets/
│       ├── css/style.css   # Stylesheet
│       └── js/main.js      # Dashboard logic
├── uploads/                # Resume storage (auto-created)
├── instance/               # SQLite database (auto-created)
└── README.md
```

## API Endpoints

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| GET    | /api/health                       | Health check             |
| GET    | /api/stats                        | Dashboard statistics     |
| GET    | /api/jobs                         | List all jobs            |
| POST   | /api/jobs                         | Create new job           |
| DELETE | /api/jobs/:id                     | Delete job               |
| POST   | /api/jobs/:id/upload              | Upload & screen resumes  |
| GET    | /api/jobs/:id/candidates          | Get candidates for job   |
| PUT    | /api/candidates/:id/shortlist     | Toggle shortlist status  |
| DELETE | /api/candidates/:id               | Delete candidate         |

---

## How the AI Works

```
Resume Text  ──┐
               ├──► TF-IDF Vectorize ──► Cosine Similarity ──► 40%
Job Desc     ──┘                                               │
                                                               ▼
Required Skills ──► Skills Overlap Score ─────────────────► 40%  ──► Final Score
                                                               │
Resume Text   ──► Experience Keyword Match ───────────────► 20%
```

**Score ≥ 60% → Auto Shortlisted**

---

*MCA Final Year Project · 2024-25*

---

## 📦 Resume Dataset (Included)

The project ships with the **Kaggle Resume Dataset** (`dataset/Resume.csv`):

| Detail | Value |
|--------|-------|
| Total Resumes | 2,484 |
| Job Categories | 24 |
| Format | CSV (`ID`, `Resume_str`, `Resume_html`, `Category`) |
| Source | Kaggle – Resume Dataset by Gaurav Dutta |

### Load the Dataset

**Via terminal:**
```bash
cd backend
python seed_data.py 10       # 10 resumes per category (240 total)
python seed_data.py 20       # 20 resumes per category (480 total)
python seed_data.py 50       # 50 resumes per category (1200 total)
```

**Via Dashboard (when running):**
Go to **Overview → "Load Dataset into System"** → choose resumes per category → click the button.

**Via API:**
```bash
curl -X POST http://localhost:5000/api/seed \
  -H "Content-Type: application/json" \
  -d '{"per_category": 10}'
```

### Categories Included
ACCOUNTANT · ADVOCATE · AGRICULTURE · APPAREL · ARTS · AUTOMOBILE · AVIATION ·
BANKING · BPO · BUSINESS-DEVELOPMENT · CHEF · CONSTRUCTION · CONSULTANT ·
DESIGNER · DIGITAL-MEDIA · ENGINEERING · FINANCE · FITNESS · HEALTHCARE ·
HR · INFORMATION-TECHNOLOGY · PUBLIC-RELATIONS · SALES · TEACHER
