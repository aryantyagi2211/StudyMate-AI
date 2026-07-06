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
    You have search results above for {LEARNER['certification']}. Use them as your ONLY source.

    Certification: {LEARNER['certification']}
    Skills to consider: {CERT['skills']}

    Look at the search results and IDENTIFY the actual topics, services, and concepts mentioned there.
    Create 10 multiple-choice questions (MCQs) about those specific topics:
    - 3-4 questions per major topic area found in the search results
    - Each question should have 4 options (A, B, C, D) — all plausible and specific
    - One correct answer per question
    - Use the skill/topic names as they appear in the search results
    - Questions must be based ONLY on the search results provided

    QUALITY REQUIREMENTS — Non-negotiable:
    1. SCENARIO-BASED: Frame questions as real-world scenarios ("An engineer needs to...") not definitions
    2. SPECIFIC: Every question must reference a concrete service, tool, command, or concept
    3. NO generic questions like "What is X?" or "Define Y" — these will be rejected
    4. NO True/False or Yes/No option pairs — all 4 options must be genuine alternatives
    5. AT LEAST 6 questions must name a specific technology (e.g., "EC2", "Kubernetes", "IAM Role")
    6. OPTIONS must be realistic and specific — not "All of the above" or "None of the above"

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
    "expected_output": "JSON object with 10 MCQ questions based on search results, each with id, skill, question text, 4 options, correct answer (A/B/C/D), and explanation."
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

    The weak skills that need teaching are listed in the context above.
    Teach them ONE BY ONE in the order they appear.

    TEACHING FLOW (repeat for each weak skill):
    1. TEACH: clear explanation + real-world example
    2. ASK: offer [DOUBT] and [NEXT] options
    3. If DOUBT: clarify, repeat until satisfied, then offer options again
    4. If NEXT: say "Moving to the next topic: [skill name]", teach it
    5. When ALL weak skills done: say "ALL TOPICS COMPLETE"

    CRITICAL: Do NOT discuss study methods, test strategies, or whether to move on.
    When student says NEXT, just move to the next skill immediately.
    """,
    "expected_output": "One skill taught at a time with real-world examples, doubt handling, and next-topic progression."
}


task_examiner = {
    "description": lambda: f"""
    You have search results above with real {LEARNER['certification']} exam content. Use them as your ONLY source.

    Certification: {LEARNER['certification']}
    Skills in scope: {CERT['skills']}

    Look at the search results and IDENTIFY the specific topics, services, and concepts mentioned.
    Create exactly 15 questions based STRICTLY on those topics:
    - 5 EASY questions (multiple choice) — about basic concepts from search results
    - 5 MEDIUM questions (multiple choice) — about deeper topics from search results
    - 5 HARD questions (open-ended Q&A style) — about complex scenarios from search results

    For MCQ questions:
    - Each has 4 options (A, B, C, D)
    - One correct answer
    - Brief explanation
    - Skill name should match what appears in search results

    For Q&A questions:
    - Open-ended question requiring detailed answer
    - Provide a model answer for comparison
    - Specify key points that should be covered

    CRITICAL: Return ONLY valid JSON in this EXACT format (no markdown, no code fences):

    {{
      "questions": [
        {{
          "id": 1,
          "type": "mcq",
          "difficulty": "easy",
          "skill": "Topic from search results",
          "question": "Question about that topic?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_answer": "B",
          "explanation": "Brief explanation"
        }},
        {{
          "id": 11,
          "type": "qa",
          "difficulty": "hard",
          "skill": "Topic from search results",
          "question": "Explain a concept from the search results?",
          "model_answer": "Detailed model answer",
          "key_points": ["Point 1", "Point 2", "Point 3"]
        }}
      ]
    }}

    Label each question with the skill/topic name as it appears in search results. After scoring, flag any skill where the student scored below 60% for more teaching.
    """,
    "expected_output": "JSON with 15 questions based on search results (10 MCQ: 5 easy + 5 medium, 5 Q&A: hard), each labeled with difficulty and skill, with answers and explanations."
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
