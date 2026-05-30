"""
Resume Parser
Extracts structured information from PDF, DOCX, and TXT resumes.
"""

import re
import os


class ResumeParser:

    EMAIL_RE    = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    PHONE_RE    = re.compile(r'(?:\+?\d[\d\s\-().]{7,14}\d)')
    NAME_RE     = re.compile(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})')

    TECH_SKILLS = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
        "swift", "kotlin", "go", "rust", "scala", "r", "matlab",
        "html", "css", "react", "angular", "vue", "node.js", "nodejs", "django",
        "flask", "spring", "express", "fastapi", "bootstrap", "tailwind",
        "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "cassandra", "dynamodb", "firebase", "elasticsearch",
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "git", "github", "gitlab", "linux",
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "nlp", "computer vision", "opencv",
        "data science", "rest api", "graphql", "microservices", "agile", "scrum",
        "big data", "hadoop", "spark", "blockchain", "iot",
    ]

    EDUCATION_KEYWORDS = [
        "b.tech", "b.e.", "btech", "bachelor", "b.sc", "bsc", "b.com",
        "m.tech", "mtech", "master", "mca", "mba", "m.sc", "msc", "phd",
        "diploma", "10th", "12th", "ssc", "hsc", "graduation", "post graduate",
        "university", "college", "institute", "school",
    ]

    SECTION_HEADERS = [
        "experience", "work experience", "employment", "professional experience",
        "internship", "projects", "education", "qualifications", "skills",
        "technical skills", "certifications", "achievements", "summary", "objective",
    ]

    # ─────────────────────────────────────────
    # Public
    # ─────────────────────────────────────────

    def parse(self, filepath: str) -> dict:
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        try:
            if ext == ".pdf":
                text = self._read_pdf(filepath)
            elif ext in (".docx", ".doc"):
                text = self._read_docx(filepath)
            else:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            print(f"[Parser] Error reading {filepath}: {e}")
            text = ""

        return {
            "text":       text,
            "name":       self._extract_name(text),
            "email":      self._extract_email(text),
            "phone":      self._extract_phone(text),
            "skills":     self._extract_skills(text),
            "education":  self._extract_education(text),
            "experience": self._extract_experience(text),
        }

    # ─────────────────────────────────────────
    # File readers
    # ─────────────────────────────────────────

    def _read_pdf(self, filepath: str) -> str:
        try:
            import pdfplumber
            text = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            return "\n".join(text)
        except ImportError:
            pass

        try:
            import PyPDF2
            text = []
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            return "\n".join(text)
        except Exception as e:
            print(f"[Parser] PDF read error: {e}")
            return ""

    def _read_docx(self, filepath: str) -> str:
        try:
            from docx import Document
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            print(f"[Parser] DOCX read error: {e}")
            return ""

    # ─────────────────────────────────────────
    # Extractors
    # ─────────────────────────────────────────

    def _extract_name(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            m = self.NAME_RE.match(line)
            if m and len(line.split()) <= 5:
                return m.group(1)
        return "Unknown Candidate"

    def _extract_email(self, text: str) -> str:
        m = self.EMAIL_RE.search(text)
        return m.group(0) if m else ""

    def _extract_phone(self, text: str) -> str:
        m = self.PHONE_RE.search(text)
        if m:
            return re.sub(r'\s+', ' ', m.group(0)).strip()
        return ""

    def _extract_skills(self, text: str) -> list:
        text_lower = text.lower()
        found = []
        for skill in self.TECH_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill.title() if len(skill) > 3 else skill.upper())
        return sorted(set(found))

    def _extract_education(self, text: str) -> str:
        lines = text.split("\n")
        edu_lines = []
        capture = False
        for line in lines:
            line_l = line.lower().strip()
            if any(kw in line_l for kw in ["education", "qualification", "academic"]):
                capture = True
            if capture and line.strip():
                if any(kw in line_l for kw in self.EDUCATION_KEYWORDS):
                    edu_lines.append(line.strip())
                if len(edu_lines) >= 6:
                    break
                # Stop if we hit another section
                if any(line_l.startswith(kw) for kw in
                       ["experience", "skills", "projects", "certification", "work"]):
                    capture = False

        if not edu_lines:
            for line in lines:
                if any(kw in line.lower() for kw in self.EDUCATION_KEYWORDS):
                    edu_lines.append(line.strip())
                if len(edu_lines) >= 4:
                    break

        return " | ".join(edu_lines[:3]) if edu_lines else ""

    def _extract_experience(self, text: str) -> str:
        lines = text.split("\n")
        exp_lines = []
        capture = False
        for line in lines:
            line_l = line.lower().strip()
            if any(kw in line_l for kw in
                   ["experience", "employment", "work history", "internship"]):
                capture = True
                continue
            if capture and line.strip():
                if any(line_l.startswith(kw) for kw in
                       ["education", "skills", "projects", "certification",
                        "achievement", "reference"]):
                    break
                exp_lines.append(line.strip())
                if len(exp_lines) >= 10:
                    break

        return " ".join(exp_lines) if exp_lines else ""
