"""
AI Engine – TF-IDF + Cosine Similarity + Skill Matching
Cloud-Based AI Resume Screening System
"""

import re
import math
from collections import Counter


class ResumeScreeningEngine:
    """
    Core AI engine using TF-IDF vectorization and cosine similarity
    to match resumes against job descriptions.
    No heavy ML libraries required – pure Python implementation.
    """

    # Comprehensive tech skills dictionary
    TECH_SKILLS = [
        # Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
        "swift", "kotlin", "go", "rust", "scala", "r", "matlab", "perl",
        # Web
        "html", "css", "react", "angular", "vue", "node.js", "nodejs", "django",
        "flask", "spring", "express", "fastapi", "bootstrap", "tailwind",
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "cassandra", "dynamodb", "firebase", "elasticsearch",
        # Cloud
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "ci/cd", "devops", "linux", "git", "github", "gitlab",
        # AI / ML
        "machine learning", "deep learning", "neural network", "tensorflow",
        "pytorch", "keras", "scikit-learn", "pandas", "numpy", "nlp",
        "computer vision", "data science", "opencv", "huggingface",
        # Concepts
        "rest api", "graphql", "microservices", "agile", "scrum", "oop",
        "data structures", "algorithms", "system design", "cloud computing",
        "cybersecurity", "blockchain", "iot", "big data", "hadoop", "spark",
    ]

    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "us", "we", "you",
        "they", "he", "she", "it", "this", "that", "these", "those", "i",
        "my", "our", "their", "your", "its", "not", "no", "nor", "so", "yet",
        "both", "either", "as", "than", "while", "although", "however",
        "therefore", "thus", "hence", "moreover", "furthermore", "also",
    }

    def __init__(self):
        self.skill_set = set(self.TECH_SKILLS)

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def calculate_match_score(
        self,
        resume_text: str,
        job_description: str,
        required_skills: list,
        candidate_skills: list
    ) -> float:
        """
        Compute weighted match score (0.0 – 1.0):
          40% → TF-IDF cosine similarity
          40% → Skills overlap
          20% → Experience keywords
        """
        if not resume_text.strip():
            return 0.0

        tfidf_score   = self._tfidf_similarity(resume_text, job_description)
        skills_score  = self._skills_score(required_skills, candidate_skills, resume_text)
        exp_score     = self._experience_score(resume_text, job_description)

        final = (tfidf_score * 0.40) + (skills_score * 0.40) + (exp_score * 0.20)
        return round(min(final, 1.0), 4)

    def extract_skills_from_text(self, text: str) -> list:
        """Return sorted list of recognised tech skills found in text."""
        text_lower = text.lower()
        found = []
        for skill in self.TECH_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill.title())
        return sorted(set(found))

    # ─────────────────────────────────────────
    # TF-IDF helpers
    # ─────────────────────────────────────────

    def _tokenize(self, text: str) -> list:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]

    def _tf(self, tokens: list) -> dict:
        count = Counter(tokens)
        total = len(tokens) or 1
        return {word: freq / total for word, freq in count.items()}

    def _idf(self, word: str, docs: list) -> float:
        containing = sum(1 for doc in docs if word in doc)
        return math.log((len(docs) + 1) / (containing + 1)) + 1

    def _tfidf_vector(self, tokens: list, all_docs: list) -> dict:
        tf = self._tf(tokens)
        return {word: tf_val * self._idf(word, all_docs) for word, tf_val in tf.items()}

    def _cosine_similarity(self, vec_a: dict, vec_b: dict) -> float:
        common = set(vec_a) & set(vec_b)
        if not common:
            return 0.0
        dot = sum(vec_a[w] * vec_b[w] for w in common)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _tfidf_similarity(self, resume: str, job_desc: str) -> float:
        r_tokens = self._tokenize(resume)
        j_tokens = self._tokenize(job_desc)
        if not r_tokens or not j_tokens:
            return 0.0
        docs = [set(r_tokens), set(j_tokens)]
        vec_r = self._tfidf_vector(r_tokens, docs)
        vec_j = self._tfidf_vector(j_tokens, docs)
        raw = self._cosine_similarity(vec_r, vec_j)
        # Sigmoid-like boost so moderate matches aren't penalised too harshly
        return min(raw * 1.5, 1.0)

    # ─────────────────────────────────────────
    # Skills scoring
    # ─────────────────────────────────────────

    def _skills_score(self, required: list, found: list, resume_text: str) -> float:
        if not required:
            # Fall back to overall skill density
            all_found = self.extract_skills_from_text(resume_text)
            return min(len(all_found) / 10, 1.0)

        req_lower = {s.lower() for s in required}
        found_lower = {s.lower() for s in found}

        # Also scan raw text for any required skills not caught by parser
        text_lower = resume_text.lower()
        for skill in req_lower:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_lower.add(skill)

        matched = req_lower & found_lower
        return len(matched) / len(req_lower)

    # ─────────────────────────────────────────
    # Experience scoring
    # ─────────────────────────────────────────

    def _experience_score(self, resume: str, job_desc: str) -> float:
        resume_lower = resume.lower()
        job_lower = job_desc.lower()

        # Extract years of experience from resume
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
            r'experience\s*(?:of\s+)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s*(?:of\s+)?(?:exp|experience)',
        ]
        resume_years = 0
        for pat in year_patterns:
            m = re.search(pat, resume_lower)
            if m:
                resume_years = int(m.group(1))
                break

        # Extract required years from job description
        required_years = 0
        for pat in year_patterns:
            m = re.search(pat, job_lower)
            if m:
                required_years = int(m.group(1))
                break

        if required_years == 0:
            exp_score = 0.6  # Neutral when requirement unspecified
        elif resume_years >= required_years:
            exp_score = 1.0
        elif resume_years > 0:
            exp_score = resume_years / required_years
        else:
            exp_score = 0.3

        # Bonus for relevant experience keywords
        keywords = ["intern", "developer", "engineer", "analyst", "scientist",
                    "lead", "senior", "junior", "associate", "specialist"]
        job_kw = [k for k in keywords if k in job_lower]
        matches = sum(1 for k in job_kw if k in resume_lower)
        keyword_bonus = (matches / len(job_kw)) * 0.3 if job_kw else 0

        return min(exp_score * 0.7 + keyword_bonus, 1.0)

    # ─────────────────────────────────────────
    # Explain score (for UI breakdown)
    # ─────────────────────────────────────────

    def explain_score(
        self,
        resume_text: str,
        job_description: str,
        required_skills: list,
        candidate_skills: list
    ) -> dict:
        tfidf  = self._tfidf_similarity(resume_text, job_description)
        skills = self._skills_score(required_skills, candidate_skills, resume_text)
        exp    = self._experience_score(resume_text, job_description)
        final  = (tfidf * 0.40) + (skills * 0.40) + (exp * 0.20)
        return {
            "tfidf_score":   round(tfidf * 100, 1),
            "skills_score":  round(skills * 100, 1),
            "exp_score":     round(exp * 100, 1),
            "final_score":   round(min(final, 1.0) * 100, 1),
            "weights":       {"tfidf": "40%", "skills": "40%", "experience": "20%"}
        }
