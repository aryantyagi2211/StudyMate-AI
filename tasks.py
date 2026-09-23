from data.data import DEMO_STUDENT, CERT_GUIDE

# Dynamic student data - set at runtime (custom or demo)
LEARNER = None  # Will be set by main.py
CERT = None     # Will be set after learner chooses certification


def _generate_skills_for_cert(certification):
    """Generate meaningful default skills for ANY certification by analyzing its name"""
    cert_upper = certification.upper()

    # -------------------- Cloud Providers --------------------
    if cert_upper.startswith("AWS"):
        return ["Compute Services", "Storage & Databases", "Networking & CDN",
                "Security & Identity", "Monitoring & Analytics", "Deployment & Automation"]
    if cert_upper.startswith("GCP") or "GOOGLE" in cert_upper:
        return ["Compute Engine", "Storage & Databases", "Networking",
                "Security & IAM", "Data & Analytics", "DevOps & Deployment"]
    if cert_upper.startswith("AZ") or "AZURE" in cert_upper:
        return ["Compute", "Storage", "Networking", "Security", "Monitoring", "Development"]
    if cert_upper.startswith("DP"):
        return ["Data Storage", "Data Processing", "Data Security", "Data Pipelines", "Data Monitoring"]
    if cert_upper.startswith("SC"):
        return ["Identity & Access", "Security Operations", "Data Protection",
                "Threat Protection", "Compliance"]

    # -------------------- DevOps / Containers / K8s --------------------
    if any(kw in cert_upper for kw in ["CKA", "CKAD", "CKS", "KUBERNETES"]):
        return ["Cluster Architecture", "Workloads & Scheduling", "Services & Networking",
                "Storage", "Security", "Troubleshooting"]
    if "DOCKER" in cert_upper:
        return ["Container Management", "Image Management", "Networking", "Security", "Orchestration"]
    if "TERRAFORM" in cert_upper:
        return ["Infrastructure as Code", "State Management", "Modules", "Provisioning", "Security"]
    if "ANSIBLE" in cert_upper:
        return ["Inventory Management", "Playbooks", "Roles", "Variables", "Automation"]
    if "DEVOPS" in cert_upper:
        return ["CI/CD", "Infrastructure as Code", "Monitoring", "Security", "Collaboration"]

    # -------------------- Linux / SysAdmin --------------------
    if any(kw in cert_upper for kw in ["RHCSA", "RHCE", "LFCS", "LINUX"]):
        return ["System Administration", "File Systems", "Networking", "Security",
                "Service Management", "Shell Scripting"]

    # -------------------- Database --------------------
    if "DATABASE" in cert_upper or "DBA" in cert_upper:
        return ["Database Design", "Query Optimization", "Backup & Recovery",
                "Security", "Performance Tuning"]
    if "ORACLE" in cert_upper or cert_upper.startswith("OC") or cert_upper.startswith("OCM"):
        return ["SQL", "Database Admin", "Backup & Recovery", "Performance Tuning", "Security"]

    # -------------------- Microsoft Legacy --------------------
    if any(kw in cert_upper for kw in ["MCSA", "MCSE", "MCSD", "MS-"]):
        return ["Server Administration", "Networking", "Security", "Active Directory", "Deployment"]

    # -------------------- Networking --------------------
    if any(kw in cert_upper for kw in ["CISCO", "CCNP", "CCIE", "NETWORK", "JNCIA", "JNCIP"]):
        return ["Network Fundamentals", "Routing & Switching", "Security",
                "Automation", "Network Access", "Troubleshooting"]
    if "CCNA" in cert_upper:
        return ["Network Fundamentals", "Routing & Switching", "Security Fundamentals",
                "Automation", "Network Access", "IP Connectivity"]

    # -------------------- Security --------------------
    if "CISSP" in cert_upper:
        return ["Security Management", "Asset Security", "Security Architecture",
                "Communication Security", "Identity Management", "Security Assessment"]
    if "CISM" in cert_upper:
        return ["Information Security Governance", "Risk Management", "Program Development",
                "Incident Management"]
    if "CISA" in cert_upper:
        return ["IS Auditing", "Governance & Management", "Acquisition & Implementation",
                "Operations & Maintenance", "Protection"]
    if any(kw in cert_upper for kw in ["CEH", "OSCP", "PENTEST", "ETHICAL"]):
        return ["Reconnaissance", "Enumeration", "Exploitation", "Post-Exploitation", "Reporting"]
    if "SECURITY" in cert_upper or "CYBER" in cert_upper:
        return ["Risk Management", "Network Security", "Identity & Access",
                "Incident Response", "Compliance"]

    # -------------------- Project Management --------------------
    if "PMP" in cert_upper or "PROJECT" in cert_upper:
        return ["Project Integration", "Scope Management", "Schedule Management",
                "Cost Management", "Risk Management", "Stakeholder Management"]
    if any(kw in cert_upper for kw in ["AGILE", "SCRUM", "CSM", "PSM", "SAFE"]):
        return ["Agile Principles", "Scrum Framework", "Sprint Planning",
                "Team Facilitation", "Continuous Improvement"]

    # -------------------- ITSM / ITIL --------------------
    if "ITIL" in cert_upper:
        return ["Service Strategy", "Service Design", "Service Transition",
                "Service Operation", "Continual Improvement"]

    # -------------------- Six Sigma / Lean --------------------
    if "SIX SIGMA" in cert_upper or "LEAN" in cert_upper:
        return ["DMAIC", "Process Mapping", "Statistical Analysis",
                "Lean Principles", "Control Plans", "Project Charter"]

    # -------------------- Enterprise Architecture --------------------
    if "TOGAF" in cert_upper:
        return ["Architecture Development", "ADM Cycle", "Enterprise Continuum",
                "Architecture Framework", "Governance"]

    # -------------------- Finance / Accounting --------------------
    if any(kw in cert_upper for kw in ["CFA", "CPA", "CMA", "FRM", "ACCA", "CIMA"]):
        return ["Financial Reporting", "Audit & Assurance", "Taxation",
                "Risk Management", "Ethics & Governance"]

    # -------------------- HR / SHRM --------------------
    if any(kw in cert_upper for kw in ["SHRM", "PHR", "SPHR", "HRCI"]):
        return ["Workforce Planning", "Talent Acquisition", "Compensation",
                "Employee Relations", "Compliance"]

    # -------------------- Data / ML / AI --------------------
    if any(kw in cert_upper for kw in ["MACHINE LEARNING", "ML ", " DATA ", "AI ",
                                       "DATA ENGINEER", "DATA SCIENTIST",
                                       "DATA ANALYTICS"]):
        return ["Data Modeling", "Data Processing", "Analytics", "ML Techniques",
                "Visualization", "Deployment"]

    # -------------------- General IT / Entry Level --------------------
    if "COMPTIA" in cert_upper:
        return ["Hardware", "Networking", "Security", "Troubleshooting", "Operational Procedures"]
    if "ITF" in cert_upper:
        return ["IT Concepts", "Infrastructure", "Applications", "Software Development", "Database"]

    # -------------------- Salesforce --------------------
    if "SALESFORCE" in cert_upper:
        return ["Salesforce Administration", "Security & Access", "Object Management",
                "Automation", "Reports & Dashboards"]

    # -------------------- Final fallback: analyze keywords --------------------
    kw_to_skills = {
        "SECURITY": ["Access Control", "Network Security", "Risk Assessment",
                     "Incident Response", "Compliance"],
        "NETWORK": ["Protocols", "Routing", "Switching", "Security", "Troubleshooting"],
        "CLOUD": ["Compute", "Storage", "Networking", "Security", "Deployment"],
        "DEVELOPER": ["Code Design", "Debugging", "Testing", "Version Control", "APIs"],
        "ADMIN": ["User Management", "Configuration", "Maintenance", "Monitoring", "Backup"],
        "ARCHITECT": ["Solution Design", "Integration", "Performance", "Security", "Cost Optimization"],
        "MANAGEMENT": ["Planning", "Execution", "Monitoring", "Risk", "Stakeholder"],
        "FOUNDATION": ["Core Concepts", "Best Practices", "Terminology", "Lifecycle", "Principles"],
        "ASSOCIATE": ["Core Concepts", "Implementation", "Troubleshooting", "Security", "Optimization"],
        "PROFESSIONAL": ["Advanced Design", "Integration", "Migration", "Security", "Optimization"],
        "EXPERT": ["Advanced Architecture", "Strategy", "Innovation", "Governance", "Leadership"],
        "MASTER": ["Enterprise Design", "Strategy", "Innovation", "Leadership", "Governance"],
        "PRACTITIONER": ["Core Practices", "Implementation", "Measurement", "Improvement", "Culture"],
    }
    for kw, skills in kw_to_skills.items():
        if kw in cert_upper:
            return skills

    return ["Core Concepts", "Architecture & Design", "Implementation",
            "Security & Compliance", "Troubleshooting", "Best Practices"]


def set_learner_data(name, role, certification):
    """Set the current learner data for this session"""
    global LEARNER, CERT
    validate_learner_data(name, role, certification)
    LEARNER = {
        "name": name,
        "role": role,
        "certification": certification
    }
    if certification in CERT_GUIDE:
        CERT = CERT_GUIDE[certification]
    else:
        CERT = {
            "full_name": f"{certification} Certification",
            "skills": _generate_skills_for_cert(certification),
            "recommended_hours": 20,
            "passing_score": 700,
            "exam_format": "Multiple choice questions",
            "difficulty": "Intermediate"
        }


def validate_learner_data(name, role, certification):
    """Validate the minimum profile and certification selection requirements."""
    values = {
        "name": name,
        "role": role,
        "certification": certification,
    }
    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string.")


def use_demo_data():
    """Load demo student data"""
    set_learner_data(
        DEMO_STUDENT["name"],
        DEMO_STUDENT["role"],
        DEMO_STUDENT["certification"]
    )


task_ceo = {
    "description": lambda: f"""
    Welcome {LEARNER['name']} to StudyMate AI.
    
    Student info:
    - Role: {LEARNER['role']}
    - Goal: {LEARNER['certification']}
    
    Give a warm, SHORT welcome (2-3 sentences) explaining the journey:
    profile → assess → learn → test → improve
    """,
    "expected_output": "Short welcome message (under 100 words) explaining the StudyMate AI process"
}


task_profiler = {
    "description": lambda: f"""
{LEARNER['name']} just signed up for {LEARNER['certification']}. They work as {LEARNER['role']}.

Get to know them - not just their cert goal. Ask naturally:
- Why do they want this cert? (career, manager said to, genuine interest, whatever)
- How are they feeling? (excited/nervous/overwhelmed/etc)
- What worries them most?

Based on their role, make a warm guess about motivation and set the tone. Keep under 150 words, one message from a real person, no headings or bullets.
    """,
    "expected_output": "A short, warm message (under 150 words) that asks about motivation, feelings, and worries in a natural, human way."
}


task_knowledge_checker = {
    "description": lambda: f"""
    Search results contain REAL PAST EXAM PAPERS for {LEARNER['certification']}. Use them as your ONLY source.

    Certification: {LEARNER['certification']}
    Skills to consider: {CERT['skills']}

    STEP 1 — ANALYZE THE PAST PAPERS:
    Look at the REAL exam questions found in the search results. Study:
    - The FORMAT of each question (how they're worded)
    - The STYLE of the options (length, specificity, distractors)
    - The DIFFICULTY level of each question
    - The TOPICS and CONCEPTS tested
    
    STEP 2 — GENERATE MATCHING QUESTIONS:
    Create 10 NEW multiple-choice questions that MATCH the exact format, style, and difficulty of the past papers.

    QUALITY REQUIREMENTS — Non-negotiable:
    1. Your questions MUST look like they came from the same exam as the past papers you found
    2. SCENARIO-BASED: Frame questions as real-world scenarios like real exams do
    3. SPECIFIC: Every question must reference a concrete service, tool, command, or concept
    4. NO generic questions like "What is X?" or "Define Y" — real exams don't ask like this
    5. NO True/False or Yes/No option pairs — all 4 options must be genuine alternatives
    6. AT LEAST 6 questions must name a specific technology (e.g., "EC2", "Kubernetes", "IAM Role")
    7. OPTIONS must be realistic and specific — not "All of the above" or "None of the above"
    8. The DIFFICULTY, WORDING LENGTH, and OPTION STRUCTURE must match the past papers

    If search results are generic or don't contain real exam questions, search AGAIN specifically for "{LEARNER['certification']} past exam questions" or "{LEARNER['certification']} question paper".

    CRITICAL: Return ONLY valid JSON in this EXACT format (no markdown, no code fences, no extra text):

    {{
      "questions": [
        {{
          "id": 1,
          "skill": "Topic Name from Search Results",
          "question": "A developer is designing a system that needs X. Which service should they use?",
          "options": ["Amazon EC2", "AWS Lambda", "Google Cloud Functions", "Azure App Service"],
          "correct_answer": "A",
          "explanation": "Brief explanation based on search results"
        }}
      ]
    }}

    The system will present these questions one by one to the student.
    """,
    "expected_output": "JSON object with 10 MCQ questions that match the style of real past exam papers, each with id, skill, question text, 4 options, correct answer (A/B/C/D), and explanation."
}

task_learning_path = {
    "description": lambda: f"""
    {LEARNER['name']} ({LEARNER['role']}) is working toward
    {LEARNER['certification']} ({CERT['full_name']}).

    Skills to focus on: {CERT['skills']}
    Recommended study hours: {CERT['recommended_hours']}

    For each skill that still needs work, point them to:
    - The most relevant official documentation or learning module
    - One great video or course
    - One well-written article or blog post
    - A hands-on exercise, sandbox, or repo to practice with
    - A community (subreddit, Discord, forum) where people discuss this topic
    - A realistic time estimate for that skill alone

    Skip any skill they're already strong in. Keep the whole thing under 250
    words and casual in tone — like a senior dev texting a junior friend a
    list of "here's what actually helped me."
    """,
    "expected_output": "A short, casual resource list (under 250 words) covering each weak skill with concrete resources and time estimates."
}


task_adaptive_plan = {
    "description": lambda: f"""
    Build a study schedule for {LEARNER['name']} that fits around their actual life.

    Certification: {LEARNER['certification']}
    Recommended study hours: {CERT['recommended_hours']}
    
    The Adaptive Planner agent will ask them directly about:
    - How many hours per day they can study
    - What time works best (morning/afternoon/evening)  
    - Any busy days they need to skip

    Build a realistic week-by-week schedule with:
    - A daily study target that fits their available time
    - Confirmation of which days are skip days
    - A 10-minute emergency plan for busy days

    Make it feel achievable and personalized to their actual constraints.
    """,
    "expected_output": "A personalized week-by-week study schedule with daily targets, skip days, and emergency plan."
}


task_teaching = {
    "description": lambda: f"""
    You are teaching {LEARNER['name']} one concept at a time for {LEARNER['certification']}.

    Certification: {LEARNER['certification']}
    All skills: {CERT['skills']}

    You MUST teach EVERY skill in order. Weak skills (listed as PRIORITY in the context above) come FIRST.
    After ALL weak skills are done, teach the remaining strong skills with DEEPER / ADVANCED concepts for each.

    TEACHING FLOW (repeat for each skill):
    1. TEACH: clear explanation + real-world example
       INCLUDE an ASCII DIAGRAM using box-drawing characters (─│┌┐└┘├┤┬┴┼) to visualize the concept
       Examples: flowchart for processes/steps, table for comparisons, tree for hierarchies, timeline for sequences
    2. ASK: offer [DOUBT] and [NEXT] options
    3. If DOUBT: clarify, repeat until satisfied, then offer options again
    4. If NEXT: say "Moving to the next topic: [skill name]", teach it
    5. When ALL skills (weak first, then strong) done: say "ALL TOPICS COMPLETE"

    DIAGRAM EXAMPLES (use these patterns):

    Flowchart:
    ┌──────────┐
    │ Step 1   │
    └────┬─────┘
         │
    ┌────▼─────┐
    │ Step 2   │
    └────┬─────┘
         │
    ┌────▼─────┐
    │ Step 3   │
    └──────────┘

    Table:
    ┌──────────┬──────────┐
    │ Header 1 │ Header 2 │
    ├──────────┼──────────┤
    │ Value 1  │ Value 2  │
    ├──────────┼──────────┤
    │ Value 3  │ Value 4  │
    └──────────┴──────────┘

    Tree:
        Root
       ╱    ╲
    Child1  Child2
      ╱╲      ╱╲
    C11 C12  C21 C22

    CRITICAL:
    - Do NOT discuss study methods, test strategies, or whether to move on.
    - When student says NEXT, just move to the next skill immediately.
    - Every skill gets at least one diagram — no exceptions.
    """,
    "expected_output": "All skills taught (weak first, then strong with advanced concepts), each with ASCII diagrams, doubt handling, and next-topic progression."
}


task_examiner = {
    "description": lambda: f"""
    Search results contain REAL PAST EXAM PAPERS for {LEARNER['certification']}. Use them as your ONLY source.

    Certification: {LEARNER['certification']}
    Skills in scope: {CERT['skills']}

    STEP 1 — ANALYZE THE PAST PAPERS:
    Study the REAL exam questions found in the search results carefully:
    - What FORMAT do they use? (scenario-based, technical, etc.)
    - What STYLE of wording? (length, technical depth)
    - What DIFFICULTY distribution? (easy vs hard topics)
    - What TYPES of options? (specific services, numbers, commands)
    
    STEP 2 — CREATE MATCHING QUESTIONS:
    Create exactly 10 questions that MATCH the EXACT style and format of the past papers:
    - 3 EASY questions — same difficulty and format as easy past paper questions
    - 4 MEDIUM questions — same difficulty and format as medium past paper questions
    - 3 HARD questions — same difficulty and format as hard past paper questions

    For each question:
    - Use the SAME wording style and complexity as real past exam questions
    - Each has 4 options (A, B, C, D) — all plausible, like real exam options
    - One correct answer
    - Brief explanation
    - Skill name should match what appears in search results

    CRITICAL RULES:
    - Questions MUST look like they're from the SAME exam as the past papers you found
    - NEVER ask "What is X" or "Define Y" — real exams don't use this format
    - Scenario-based only — like real certification exams
    - NO "All of the above" / "None of the above" options
    - NO True/False or Yes/No pairs

    If search results don't contain real exam questions, search again specifically for "{LEARNER['certification']} previous year question paper".

    Present each question ONE AT A TIME to the student in a clean format:

    Question 1: [EASY]
    [question text]
    A) [option A]
    B) [option B]
    C) [option C]
    D) [option D]

    After the student answers, tell them if correct/incorrect and briefly explain. Do NOT use JSON format."""
}


task_manager_insights = {
    "description": lambda: f"""
    Put together a report on {LEARNER['name']}'s session so the CEO can decide what happens next.

    Student: {LEARNER['name']} ({LEARNER['role']})
    Certification: {LEARNER['certification']}

    Write three short sections:
    1. How did they do? — What went well, where did they struggle?
    2. What needs attention? — Which skills are still weak?
    3. Recommendation — Should they go back to Teaching for more explanation, Examiner for more practice, or are they ready to move on?

    Keep it short enough that the CEO can act on it immediately.
    """,
    "expected_output": "A 3-part report — performance summary, attention areas, and a clear recommendation."
}
