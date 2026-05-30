"""
Improved scoring helper for seed_data.py
Uses domain-aware skill matching tuned to the Kaggle resume dataset.
"""
import re, math
from collections import Counter

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
    "from","is","are","was","were","be","been","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","not","no",
    "us","we","you","they","he","she","it","this","that","these","those","i",
    "my","our","their","your","its","as","than","while","also","both","so",
    "name","city","state","date","current","company","position",
}

# Comprehensive multi-domain skills
ALL_SKILLS = [
    # Tech
    "python","java","javascript","typescript","c++","c#","ruby","php","swift","golang",
    "html","css","react","angular","vue","nodejs","django","flask","spring","fastapi",
    "sql","mysql","postgresql","mongodb","redis","sqlite","oracle","elasticsearch",
    "aws","gcp","azure","docker","kubernetes","terraform","jenkins","git","linux",
    "machine learning","deep learning","tensorflow","pytorch","scikit-learn",
    "pandas","numpy","nlp","data science","rest api","microservices","agile","scrum",
    "network","security","cybersecurity","microsoft","windows","server","systems",
    "software","hardware","technical support","information technology","database",
    # Finance / Accounting
    "accounting","financial","finance","excel","quickbooks","sap","budgeting","audit",
    "tax","gaap","forecasting","accounts payable","accounts receivable","balance sheet",
    "financial reporting","financial analysis","investment","banking","payroll",
    "bookkeeping","general ledger","erp","oracle financials","cash flow",
    # HR
    "recruitment","talent acquisition","employee relations","performance management",
    "human resources","onboarding","benefits","compensation","hris","workforce",
    "training","employee","staff","hiring","interviewing","retention","culture",
    # Sales / Marketing
    "sales","customer service","crm","lead generation","business development",
    "marketing","social media","digital marketing","seo","content","email marketing",
    "brand","advertising","market research","product","retail","customer",
    "salesforce","b2b","b2c","revenue","pipeline","negotiation","closing",
    # Healthcare
    "patient care","healthcare","medical","clinical","nursing","hospital","emr",
    "hipaa","diagnosis","treatment","pharmacy","surgery","therapy","health",
    "patient","doctor","physician","medication","compliance","regulatory",
    # Engineering
    "engineering","autocad","solidworks","manufacturing","quality control",
    "mechanical","electrical","civil","project management","design","cad",
    "process","equipment","testing","maintenance","technical","production",
    # Legal
    "legal","litigation","law","court","compliance","contract","attorney","advocate",
    "legal research","drafting","arbitration","criminal law","civil law","brief",
    # Banking / Finance
    "loans","credit","risk management","banking","investment","portfolio","trading",
    "financial planning","wealth management","insurance","underwriting","aml","kyc",
    # Design
    "photoshop","illustrator","figma","adobe","graphic design","ui","ux","typography",
    "branding","visual","creative","design","sketch","indesign","layout",
    # Digital Media
    "social media","content creation","digital","seo","google analytics","wordpress",
    "video","photography","editing","copywriting","blogging","influencer",
    # Chef / Culinary
    "culinary","chef","kitchen","food","restaurant","menu","catering","cooking",
    "food safety","haccp","inventory","sous chef","pastry","hospitality",
    # Construction
    "construction","project management","site management","osha","blueprints",
    "estimating","contractor","safety","building","structural","planning",
    # Agriculture
    "agriculture","farming","crop","soil","irrigation","agronomy","livestock",
    "horticulture","research","plant","harvest","sustainability","gis",
    # Aviation
    "aviation","flight","aircraft","faa","pilot","navigation","airline","safety",
    "air traffic","maintenance","regulatory","aerospace",
    # Automobile
    "automotive","vehicle","engine","mechanical","diagnostics","repair","automobile",
    "electrical systems","transmission","maintenance","workshop",
    # BPO
    "customer service","call center","bpo","communication","data entry","helpdesk",
    "inbound","outbound","crm","troubleshooting","escalation","ticket",
    # Education
    "teaching","curriculum","classroom","education","student","lesson planning",
    "assessment","mentoring","e-learning","instruction","academic","faculty",
    # Fitness
    "fitness","personal training","nutrition","wellness","exercise","coaching",
    "group fitness","weight training","cardio","rehabilitation","health",
    # Public Relations
    "public relations","media relations","press release","crisis communications",
    "brand management","writing","communications","journalism","spokesperson",
    # Arts
    "illustration","fine arts","painting","photography","video","creative",
    "portfolio","exhibition","sculpture","animation","film",
    # Apparel / Fashion
    "fashion","textile","pattern making","merchandising","apparel","garment",
    "fashion design","production","trend","retail","buying",
    # Consultant
    "consulting","strategy","advisory","analysis","stakeholder","process improvement",
    "change management","presentation","deliverable","framework","transformation",
    # Soft skills
    "leadership","communication","teamwork","problem solving","analytical",
    "management","coordination","planning","organization","multitasking",
]

def extract_skills(text):
    tl = text.lower()
    found = []
    for sk in ALL_SKILLS:
        if re.search(r'\b' + re.escape(sk) + r'\b', tl):
            found.append(sk.title() if len(sk.split()) > 1 else
                         sk.upper() if len(sk) <= 3 else sk.title())
    return sorted(set(found))

def _tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return [t for t in text.split() if t not in STOPWORDS and len(t) > 2]

def _tf(tokens):
    c = Counter(tokens)
    total = len(tokens) or 1
    return {w: f/total for w, f in c.items()}

def _cosine(a, b):
    common = set(a) & set(b)
    if not common: return 0.0
    dot  = sum(a[w]*b[w] for w in common)
    ma   = math.sqrt(sum(v**2 for v in a.values()))
    mb   = math.sqrt(sum(v**2 for v in b.values()))
    return dot/(ma*mb) if ma and mb else 0.0

def _tfidf_sim(resume, jd):
    rt, jt = _tokenize(resume), _tokenize(jd)
    if not rt or not jt: return 0.0
    docs = [set(rt), set(jt)]
    def vec(tokens):
        tf = _tf(tokens)
        return {w: tf[w]*(math.log(3/(sum(1 for d in docs if w in d)+1))+1)
                for w in tf}
    raw = _cosine(vec(rt), vec(jt))
    return min(raw * 2.2, 1.0)           # generous boost for short JDs

def _skills_score(required, found, text):
    if not required:
        return min(len(found)/8, 1.0)
    req = {s.lower() for s in required}
    fnd = {s.lower() for s in found}
    tl  = text.lower()
    for sk in req:
        if re.search(r'\b' + re.escape(sk) + r'\b', tl):
            fnd.add(sk)
    matched = req & fnd
    # partial credit: count words inside multi-word skills
    bonus = 0
    for r_sk in req - matched:
        words = r_sk.split()
        if len(words) > 1 and any(w in tl for w in words if len(w) > 3):
            bonus += 0.4
    return min((len(matched) + bonus) / len(req), 1.0)

def _exp_score(text):
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
        r'experience\s*(?:of\s+)?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?',
    ]
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            yrs = int(m.group(1))
            return min(yrs / 6, 1.0)
    return 0.45     # neutral when not found

def quick_score(resume_text, jd_text, required_skills, found_skills):
    t  = _tfidf_sim(resume_text, jd_text)
    sk = _skills_score(required_skills, found_skills, resume_text)
    ex = _exp_score(resume_text)
    return round(min(t*0.40 + sk*0.40 + ex*0.20, 1.0), 4)
