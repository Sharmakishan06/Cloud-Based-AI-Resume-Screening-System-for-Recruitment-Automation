"""
Dataset Seeder  –  Resume.csv  →  SQLite
Run:  python seed_data.py [resumes_per_category]   (default 10)
"""

import sqlite3, csv, json, os, re, sys
from datetime import datetime
from _seed_score import quick_score, extract_skills

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, '..', 'instance', 'screening.db')
CSV_PATH = os.path.join(BASE_DIR, '..', 'dataset',  'Resume.csv')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ── Job definitions aligned with real resume vocabulary ─────────
JOB_DEFS = {
    "INFORMATION-TECHNOLOGY": {
        "title": "IT Systems & Software Professional",
        "description": (
            "We are looking for an Information Technology professional with strong technical "
            "background in systems, software development, network administration, and security. "
            "The candidate should have experience in IT support, server management, software "
            "solutions, data analysis, cybersecurity, and enterprise IT infrastructure. "
            "Proficiency in Microsoft technologies, database systems, and technical troubleshooting "
            "is essential. Ability to manage systems and provide technical support required."
        ),
        "skills": ["Information Technology","Systems","Network","Security","Microsoft",
                   "Server","Software","Database","Technical Support","Linux","Python",
                   "SQL","Data","Git","Cybersecurity","Cloud"],
        "exp": 2,
    },
    "FINANCE": {
        "title": "Finance & Accounting Specialist",
        "description": (
            "Seeking a finance professional with strong knowledge of financial analysis, "
            "accounting principles, budgeting, forecasting, and financial reporting. "
            "Experience with accounts payable, accounts receivable, general ledger, "
            "balance sheet preparation, cash flow management, and audit. "
            "Proficiency in Excel, SAP, QuickBooks, and financial modelling required. "
            "CPA or equivalent certification preferred. Strong understanding of GAAP."
        ),
        "skills": ["Financial","Accounting","Excel","Budgeting","Forecasting","Audit",
                   "Tax","GAAP","Financial Reporting","SAP","QuickBooks","Analysis",
                   "Accounts Payable","General Ledger","Cash Flow","Investment"],
        "exp": 3,
    },
    "HEALTHCARE": {
        "title": "Healthcare & Medical Professional",
        "description": (
            "Looking for a healthcare professional with clinical experience in patient care, "
            "medical services, health management, and treatment coordination. Experience with "
            "hospital operations, medical documentation, patient management, healthcare "
            "compliance, and staff training. Knowledge of EMR systems, HIPAA regulations, "
            "diagnosis, medication management, and quality healthcare service delivery required."
        ),
        "skills": ["Patient Care","Healthcare","Medical","Clinical","Health","Hospital",
                   "Patient","Nursing","EMR","HIPAA","Treatment","Diagnosis","Staff",
                   "Compliance","Training","Customer Service"],
        "exp": 2,
    },
    "ENGINEERING": {
        "title": "Engineering & Technical Professional",
        "description": (
            "We need an engineering professional with hands-on experience in systems design, "
            "manufacturing, quality control, project management, and technical analysis. "
            "Strong background in mechanical, electrical, or software engineering. "
            "Proficiency in AutoCAD, SolidWorks, technical documentation, and equipment "
            "maintenance. Experience in process improvement, testing, and production management."
        ),
        "skills": ["Engineering","Project Management","Quality Control","Design","AutoCAD",
                   "Manufacturing","Technical","Equipment","Process","Testing","Maintenance",
                   "Systems","Mechanical","Electrical","Production","CAD"],
        "exp": 2,
    },
    "BANKING": {
        "title": "Banking & Financial Services Professional",
        "description": (
            "Seeking a banking professional with expertise in financial services, credit analysis, "
            "risk management, loans, client relationship management, and sales. "
            "Experience in banking operations, compliance, investment products, "
            "and financial planning. Strong analytical, customer service, and communication "
            "skills required. Knowledge of AML, KYC, and banking regulations essential."
        ),
        "skills": ["Banking","Financial","Sales","Credit","Risk Management","Loans",
                   "Customer Service","Client","Investment","Compliance","AML","KYC",
                   "Analysis","Management","Business Development","CRM"],
        "exp": 2,
    },
    "SALES": {
        "title": "Sales & Business Development Executive",
        "description": (
            "Looking for a target-driven sales executive with proven experience in "
            "customer acquisition, account management, and revenue generation. "
            "Strong skills in customer service, CRM, product knowledge, lead generation, "
            "and retail or B2B sales. Ability to meet targets, manage pipelines, "
            "train sales staff, and build long-term customer relationships required."
        ),
        "skills": ["Sales","Customer Service","CRM","Business Development","Customer",
                   "Retail","Product","Training","Lead Generation","Account Management",
                   "Revenue","Negotiation","B2B","Communication","Marketing","Manager"],
        "exp": 1,
    },
    "HR": {
        "title": "Human Resources Professional",
        "description": (
            "Seeking an HR professional with strong experience in recruitment, talent acquisition, "
            "employee relations, performance management, and payroll. Knowledge of HR policies, "
            "onboarding, benefits administration, workforce planning, training, and compliance "
            "required. Experience with HRIS systems, employee engagement, and labour law. "
            "Strong communication and people management skills essential."
        ),
        "skills": ["Human Resources","Recruitment","Employee","Training","Payroll",
                   "Performance Management","Benefits","Onboarding","Staff","Policies",
                   "Talent Acquisition","Workforce","HRIS","Compliance","Communication",
                   "Employee Relations","Hiring","Retention"],
        "exp": 2,
    },
    "BUSINESS-DEVELOPMENT": {
        "title": "Business Development Manager",
        "description": (
            "Looking for a business development professional with expertise in strategic growth, "
            "client acquisition, partnership development, and revenue generation. "
            "Strong background in market analysis, proposal writing, sales strategy, "
            "CRM management, and client relationship management. Experience in B2B "
            "business development, stakeholder engagement, and project management preferred."
        ),
        "skills": ["Business Development","Sales","Client","Market","Strategy","CRM",
                   "Revenue","Development","Management","Project","Analysis","Customer",
                   "Communication","Negotiation","Partnership","Planning"],
        "exp": 3,
    },
    "CONSULTANT": {
        "title": "Management Consultant",
        "description": (
            "Seeking a consultant with strong analytical skills, strategy expertise, and "
            "experience in process improvement and client advisory. Background in management "
            "consulting, business analysis, stakeholder management, and project delivery. "
            "Excellent presentation, communication, and problem-solving skills. "
            "Experience with data analysis, change management, and strategic planning."
        ),
        "skills": ["Consulting","Strategy","Analysis","Project Management","Client",
                   "Business","Management","Process","Communication","Planning",
                   "Stakeholder","Advisory","Development","Problem Solving","Presentation"],
        "exp": 3,
    },
    "DESIGNER": {
        "title": "Graphic & UI/UX Designer",
        "description": (
            "Creative designer needed with strong skills in graphic design, visual communication, "
            "and UI/UX design. Proficiency in Adobe Photoshop, Illustrator, Figma, and InDesign. "
            "Experience in branding, marketing design, product design, and creative project "
            "management. Strong portfolio demonstrating typography, layout, and visual "
            "design skills across digital and print media."
        ),
        "skills": ["Design","Graphic Design","Photoshop","Illustrator","Figma","Adobe",
                   "Creative","Visual","Branding","UI","UX","Typography","Layout",
                   "Marketing","Project","Product","Client"],
        "exp": 1,
    },
    "DIGITAL-MEDIA": {
        "title": "Digital Media & Marketing Specialist",
        "description": (
            "Seeking a digital media professional with expertise in social media management, "
            "content creation, SEO, digital marketing, and online advertising. "
            "Experience with Google Analytics, WordPress, email marketing, and content strategy. "
            "Strong writing, video production, and photography skills. "
            "Knowledge of brand management, digital campaigns, and audience analytics required."
        ),
        "skills": ["Digital","Social Media","Content","Marketing","SEO","Google Analytics",
                   "WordPress","Writing","Video","Photography","Brand","Advertising",
                   "Email Marketing","Digital Marketing","Creative","Communication"],
        "exp": 1,
    },
    "ACCOUNTANT": {
        "title": "Senior Accountant / CPA",
        "description": (
            "Looking for a qualified accountant with CPA or equivalent certification, "
            "strong knowledge of GAAP, tax preparation, financial statements, and audit. "
            "Experience in accounts payable, accounts receivable, payroll, general ledger, "
            "bookkeeping, and financial reporting. Proficiency in QuickBooks, SAP, and Excel. "
            "Ability to manage full-cycle accounting and support financial decision-making."
        ),
        "skills": ["Accounting","Financial","Tax","Excel","QuickBooks","Audit","GAAP",
                   "Payroll","Bookkeeping","General Ledger","SAP","Budgeting",
                   "Accounts Payable","Financial Statements","Reporting","Analysis"],
        "exp": 3,
    },
    "ADVOCATE": {
        "title": "Legal Advocate & Client Services Professional",
        "description": (
            "Seeking an advocate or customer-facing professional with strong client service, "
            "communication, and case management skills. Experience in client advocacy, "
            "legal services, customer care, sales support, or community services. "
            "Ability to handle customer inquiries, provide information, manage caseloads, "
            "train staff, and maintain high service quality standards required."
        ),
        "skills": ["Customer Service","Client","Sales","Advocate","Training","Staff",
                   "Communication","Information","Management","Care","Customers",
                   "Services","Office","Education","Support","Team"],
        "exp": 1,
    },
    "AVIATION": {
        "title": "Aviation Operations Professional",
        "description": (
            "Looking for an aviation professional with experience in flight operations, "
            "airline operations management, safety compliance, and regulatory adherence. "
            "Background in aircraft maintenance, navigation, air traffic coordination, "
            "or airline customer service. FAA certification knowledge and safety management "
            "systems experience preferred. Strong attention to detail required."
        ),
        "skills": ["Aviation","Flight","Safety","Operations","Aircraft","Navigation",
                   "Regulatory","Compliance","Airline","Maintenance","Customer Service",
                   "Management","Training","Technical","Team"],
        "exp": 2,
    },
    "CHEF": {
        "title": "Head Chef / Culinary Manager",
        "description": (
            "Seeking an experienced chef with strong culinary skills and kitchen management "
            "experience. Background in menu planning, food safety, restaurant operations, "
            "and staff training. Experience managing kitchen inventory, maintaining "
            "quality standards, and delivering excellent food service. Knowledge of "
            "HACCP food safety standards. Customer service and team leadership skills required."
        ),
        "skills": ["Chef","Culinary","Kitchen","Food","Restaurant","Menu","Food Safety",
                   "Catering","Staff","Training","Inventory","Customer Service",
                   "Management","Quality","Team","HACCP","Hospitality"],
        "exp": 2,
    },
    "CONSTRUCTION": {
        "title": "Construction Project Manager / Site Supervisor",
        "description": (
            "Looking for a construction professional with strong project management, "
            "site supervision, and safety compliance experience. Background in construction "
            "project planning, budgeting, contractor coordination, and quality control. "
            "Knowledge of OSHA safety standards, building codes, and construction drawings. "
            "Experience with scheduling, estimating, and managing construction teams."
        ),
        "skills": ["Construction","Project Management","Safety","Site","OSHA","Budgeting",
                   "Quality Control","Planning","Management","Team","Technical",
                   "Scheduling","Estimating","Building","Compliance","Equipment"],
        "exp": 3,
    },
    "AGRICULTURE": {
        "title": "Agricultural Research & Development Specialist",
        "description": (
            "Seeking an agricultural specialist with expertise in crop science, research, "
            "education and training, program development, and data analysis. "
            "Experience in university or government agricultural programs, soil science, "
            "irrigation, sustainability, and agricultural extension services. "
            "Strong research, analytical, and community engagement skills required."
        ),
        "skills": ["Agriculture","Research","Development","Education","Training","Data",
                   "Science","Program","University","System","Crop","Soil","Sustainability",
                   "Analysis","Management","Planning","Technical"],
        "exp": 2,
    },
    "AUTOMOBILE": {
        "title": "Automotive Technician / Engineer",
        "description": (
            "Looking for an automotive professional with expertise in vehicle diagnostics, "
            "mechanical and electrical repair, engine servicing, and quality inspection. "
            "Experience with CAD design, manufacturing processes, automotive engineering, "
            "and workshop management. Strong technical and problem-solving skills. "
            "Knowledge of automotive systems, safety, and quality standards required."
        ),
        "skills": ["Automotive","Vehicle","Mechanical","Engine","Diagnostics","Electrical",
                   "Maintenance","Repair","Quality","Technical","CAD","Manufacturing",
                   "Safety","Design","Systems","Workshop"],
        "exp": 2,
    },
    "BPO": {
        "title": "BPO / Customer Service & Operations Executive",
        "description": (
            "Seeking a BPO professional with strong customer service, communication, "
            "and process management skills. Experience in call centre operations, "
            "inbound and outbound calling, CRM, data entry, and issue resolution. "
            "Ability to meet service targets, manage escalations, maintain customer "
            "satisfaction, and support team operations required."
        ),
        "skills": ["Customer Service","Communication","CRM","Call Center","BPO",
                   "Data Entry","Inbound","Outbound","Team","Management","Training",
                   "Quality","Support","Problem Solving","Operations","MS Office"],
        "exp": 1,
    },
    "FITNESS": {
        "title": "Fitness Trainer & Wellness Coach",
        "description": (
            "Looking for a certified fitness trainer with expertise in personal training, "
            "nutrition counselling, group fitness, and wellness coaching. Experience with "
            "fitness assessments, exercise programming, weight training, cardio, and "
            "rehabilitation. CPR certified. Strong client management, health education, "
            "and motivation skills. Customer service and communication skills essential."
        ),
        "skills": ["Fitness","Personal Training","Nutrition","Wellness","Exercise",
                   "Coaching","Health","Group Fitness","Training","Customer Service",
                   "Weight Training","Cardio","CPR","Assessment","Communication","Team"],
        "exp": 1,
    },
    "PUBLIC-RELATIONS": {
        "title": "Public Relations & Communications Specialist",
        "description": (
            "Seeking a PR professional with expertise in media relations, press release writing, "
            "brand communications, crisis management, and stakeholder engagement. "
            "Strong writing and editing skills. Experience in social media, digital communications, "
            "event management, and brand management. Knowledge of journalism, SEO, and "
            "public communications strategy required."
        ),
        "skills": ["Public Relations","Media Relations","Writing","Communications","Brand",
                   "Press Release","Social Media","Digital","SEO","Crisis Communication",
                   "Management","Marketing","Journalism","Events","Strategy","Team"],
        "exp": 2,
    },
    "TEACHER": {
        "title": "Teacher & Academic Educator",
        "description": (
            "Looking for a qualified teacher with experience in curriculum development, "
            "classroom management, and student assessment. Strong subject knowledge and "
            "ability to create engaging lesson plans. Experience with educational technology, "
            "e-learning, mentoring, and student counselling. Excellent communication, "
            "patience, and academic instruction skills. University or school teaching experience."
        ),
        "skills": ["Teaching","Curriculum","Education","Students","Classroom","Assessment",
                   "Lesson Planning","Mentoring","Training","Communication","Academic",
                   "University","School","Instruction","Development","Management"],
        "exp": 1,
    },
    "ARTS": {
        "title": "Creative Arts & Media Professional",
        "description": (
            "Seeking a creative professional with experience in fine arts, illustration, "
            "photography, video production, or performing arts. Strong portfolio demonstrating "
            "creative work. Proficiency in Adobe Creative Suite, digital art tools, "
            "and visual storytelling. Experience in exhibitions, creative direction, "
            "client projects, and arts education or community engagement."
        ),
        "skills": ["Creative","Design","Photography","Video","Illustration","Arts",
                   "Adobe","Portfolio","Visual","Photoshop","Marketing","Social Media",
                   "Communication","Management","Education","Client","Team"],
        "exp": 1,
    },
    "APPAREL": {
        "title": "Fashion & Apparel Design Professional",
        "description": (
            "Looking for a fashion and apparel professional with expertise in garment design, "
            "pattern making, textile sourcing, and production management. "
            "Experience in fashion merchandising, trend analysis, retail buying, and "
            "brand development. Proficiency in Adobe Illustrator, fashion design software, "
            "and production planning. Strong creative, communication, and business skills."
        ),
        "skills": ["Fashion","Design","Apparel","Textile","Pattern","Merchandising",
                   "Retail","Production","Brand","Marketing","Creative","Management",
                   "Illustrator","Adobe","Sales","Communication","Trend"],
        "exp": 2,
    },
}

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()[:5000]

def extract_name(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    headers = {'SUMMARY','SKILL','EXPERIENCE','EDUCATION','OBJECTIVE','PROFILE',
               'CAREER','WORK','PROFESSIONAL','TECHNICAL','CERTIFICATION'}
    for line in lines[:6]:
        words = line.split()
        if 2 <= len(words) <= 4:
            if line[0].isupper() and not any(w.upper() in headers for w in words):
                if not re.search(r'[@\d/]', line):
                    return line.title()
    return f"Candidate {lines[0][:20].title()}" if lines else "Candidate"

def extract_email(text):
    m = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    return m.group(0) if m else ""

def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT,
            experience_years INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT, email TEXT, phone TEXT,
            filename TEXT, extracted_text TEXT,
            skills TEXT, experience TEXT, education TEXT,
            match_score REAL DEFAULT 0.0,
            rank_position INTEGER DEFAULT 0,
            shortlisted INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
    """)
    conn.commit()

def seed(csv_path, db_path, n=10):
    print(f"\n📂 Reading: {csv_path}")
    with open(csv_path, encoding='utf-8', errors='ignore') as f:
        all_rows = list(csv.DictReader(f))
    print(f"   Total resumes: {len(all_rows)} across categories\n")

    conn = sqlite3.connect(db_path)
    init_db(conn)
    cur = conn.cursor()

    # Clear previous dataset entries
    cur.execute("DELETE FROM candidates WHERE filename LIKE 'dataset_%'")
    cur.execute("DELETE FROM jobs WHERE title LIKE '%[Dataset]%'")
    conn.commit()

    from collections import defaultdict
    by_cat = defaultdict(list)
    for r in all_rows:
        by_cat[r['Category'].strip().upper()].append(r)

    grand_total = 0
    category_summary = []

    for cat in sorted(by_cat.keys()):
        if cat not in JOB_DEFS:
            print(f"  ⚠️  No definition for {cat}, skipping.")
            continue

        jd      = JOB_DEFS[cat]
        sample  = by_cat[cat][:n]

        # Insert job
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(
            "INSERT INTO jobs (title,description,required_skills,experience_years,created_at) VALUES(?,?,?,?,?)",
            (f"{jd['title']} [Dataset]", jd['description'],
             json.dumps(jd['skills']), jd['exp'], now)
        )
        job_id = cur.lastrowid

        scored = []
        for i, res in enumerate(sample):
            raw  = res.get('Resume_str','')
            text = clean_text(raw)
            name  = extract_name(raw)
            email = extract_email(raw)
            skls  = extract_skills(text)
            score = quick_score(text, jd['description'], jd['skills'], skls)
            scored.append((name, email, text, skls, score, i+1))

        scored.sort(key=lambda x: x[4], reverse=True)

        for rank, (name, email, text, skls, score, orig_i) in enumerate(scored, 1):
            cur.execute("""
                INSERT INTO candidates
                (job_id,name,email,phone,filename,extracted_text,
                 skills,experience,education,match_score,rank_position,shortlisted,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                job_id, name, email, "",
                f"dataset_{cat.lower()}_{rank}.txt",
                text, json.dumps(skls), "", "",
                round(score*100, 2), rank,
                1 if score >= 0.55 else 0,
                now
            ))

        conn.commit()
        top   = max(s[4] for s in scored) * 100
        short = sum(1 for s in scored if s[4] >= 0.55)
        avg   = sum(s[4] for s in scored) / len(scored) * 100
        grand_total += len(scored)
        category_summary.append((cat, len(scored), top, avg, short))
        print(f"  ✅ {cat:<26} {len(scored):>3} resumes │ top {top:5.1f}% │ avg {avg:5.1f}% │ shortlisted {short}")

    conn.close()

    print(f"\n{'─'*70}")
    print(f"  🎉  Seeded {grand_total} resumes across {len(category_summary)} job categories")
    print(f"  📊  Overall avg score: {sum(r[3] for r in category_summary)/len(category_summary):.1f}%")
    print(f"  ✅  Total shortlisted: {sum(r[4] for r in category_summary)}")
    print(f"{'─'*70}\n")

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    if not os.path.exists(CSV_PATH):
        print(f"❌  CSV not found at: {CSV_PATH}")
        print(f"    Place Resume.csv in: {os.path.dirname(CSV_PATH)}")
        sys.exit(1)
    seed(CSV_PATH, DB_PATH, n)
