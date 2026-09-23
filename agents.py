"""
Agents that talk to LLMs (Groq / OpenRouter) and optionally search the web.
"""

from openai import AsyncOpenAI, RateLimitError
from dotenv import load_dotenv
import os
import asyncio
import random
import re

load_dotenv()

MODEL_TIMEOUT_SECONDS = float(os.getenv("STUDYMATE_MODEL_TIMEOUT_SECONDS", "45"))
MODEL_MAX_RETRIES = int(os.getenv("STUDYMATE_MODEL_MAX_RETRIES", "3"))

# ── Groq setup ──────────────────────────────────────────────────────────
def _load_api_keys():
    keys = []
    # Named env vars: GROQ_API_KEY, GROQ_API_KEY_2, etc.
    for name in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GROQ_API_KEY_5"]:
        val = os.getenv(name)
        if val:
            keys.extend(k.strip() for k in val.split(",") if k.strip())
    return list(dict.fromkeys(keys))  # deduplicate preserving order

GROQ_KEYS = _load_api_keys()
GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]

if GROQ_KEYS:
    print(f"[API] Groq: {len(GROQ_KEYS)} key(s) loaded")

# ── OpenRouter setup ────────────────────────────────────────────────────
ROUTER_KEY = os.getenv("ROUTER_API_KEY")
ROUTER_MODELS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

AUTHORITATIVE_SOURCE_DOMAINS = {
    "AWS": ("docs.aws.amazon.com", "aws.amazon.com"),
    "AZURE": ("learn.microsoft.com", "azure.microsoft.com"),
    "AZ-": ("learn.microsoft.com", "azure.microsoft.com"),
    "GCP": ("cloud.google.com",),
    "GOOGLE": ("cloud.google.com",),
    "KUBERNETES": ("kubernetes.io",),
    "CISCO": ("cisco.com",),
    "CCNA": ("cisco.com",),
    "CISSP": ("isc2.org",),
    "COMPTIA": ("comptia.org",),
    "RED HAT": ("redhat.com",),
    "LINUX FOUNDATION": ("training.linuxfoundation.org",),
    "PMP": ("pmi.org",),
    "ORACLE": ("oracle.com",),
}


def get_authoritative_source_domains(certification: str) -> tuple[str, ...]:
    """Return official domains to prioritize for a certification."""
    normalized = certification.upper()
    for keyword, domains in AUTHORITATIVE_SOURCE_DOMAINS.items():
        if keyword in normalized:
            return domains
    return ()


def add_authoritative_source_filter(query: str, certification: str) -> str:
    """Prefer official documentation without excluding unknown certifications."""
    domains = get_authoritative_source_domains(certification)
    if not domains:
        return query
    return f"{query} ({' OR '.join(f'site:{domain}' for domain in domains)})"

if ROUTER_KEY:
    print("[API] OpenRouter: loaded")

# ── Provider selection ──────────────────────────────────────────────────
PROVIDER_WEIGHTS = []
if GROQ_KEYS:
    PROVIDER_WEIGHTS.append("groq")
if ROUTER_KEY:
    PROVIDER_WEIGHTS.append("openrouter")


def get_runtime_status():
    """Return a safe, serializable view of the model configuration."""
    return {
        "groq_keys_loaded": len(GROQ_KEYS),
        "openrouter_key_loaded": bool(ROUTER_KEY),
        "providers": list(PROVIDER_WEIGHTS),
        "configured": bool(PROVIDER_WEIGHTS),
    }


def validate_runtime_config():
    """Fail only at runtime with a clear message when the app is missing keys."""
    if not PROVIDER_WEIGHTS:
        raise ValueError("No AI provider keys found. Add GROQ_API_KEY or ROUTER_API_KEY to your .env file and restart the app.")
    return get_runtime_status()


def get_client_and_model():
    """Pick a random provider and return (AsyncOpenAI, model_name)."""
    validate_runtime_config()
    provider = random.choice(PROVIDER_WEIGHTS)

    if provider == "openrouter":
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=ROUTER_KEY,
            timeout=MODEL_TIMEOUT_SECONDS,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "StudyMate AI",
            },
        )
        model = random.choice(ROUTER_MODELS)
    else:
        api_key = random.choice(GROQ_KEYS)
        client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            timeout=MODEL_TIMEOUT_SECONDS,
        )
        model = random.choice(GROQ_MODELS)

    return client, model, provider


class SimpleAgent:
    def __init__(self, name, description, instructions, reasoning=False, enable_tools=False):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.reasoning = reasoning
        self.enable_tools = enable_tools
        self.last_sources = []

    def get_last_sources(self):
        """Return the source records used by the most recent search."""
        return [dict(source) for source in self.last_sources]
        
    def create_session(self):
        """Create a new conversation session"""
        return [] 
    
    def _build_reasoning_prompt(self, prompt: str) -> str:
        """Add chain-of-thought reasoning to the prompt"""
        # Check if this agent needs pure output (JSON, etc.)
        needs_pure_output = any(keyword in self.instructions.lower() for keyword in [
            "return only valid json",
            "only json",
            "must return only",
            "critical: you must return only"
        ])
        
        if needs_pure_output:
            return prompt
        
        # Flatten reasoning into rough string - not too structured
        reasoning_template = """Think step-by-step: What's the student asking? What do I know about their level? What approach makes sense here? How should I respond? Now answer: {prompt}"""
        
        return reasoning_template.format(prompt=prompt)
    
    def _extract_cert(self, prompt: str) -> str:
        """Extract certification code from prompt — works for ANY certification"""
        text = self.instructions + prompt

        # 1. Numbered cert codes: AWS-SAA, AZ-204, DP-203, CLF-C01, etc
        match = re.search(r'([A-Z]{2,6}-\d{3,4})', text)
        if match:
            return match.group(1)

        # 2. Any hyphenated cert name (wide range): AWS-SAA, TESTING-CLASSIFICATION, COMPTIA-SECURITY-PLUS
        #    Must be at least 2 uppercase letters on each side, up to 20
        match = re.search(r'([A-Z]{2,20}-[A-Z]{2,20}(?:-[A-Z]{2,20})?)', text)
        if match:
            return match.group(1)

        # 3. Multi-word cert in "for X certification" pattern
        match = re.search(r'for\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)\s+[Cc]ert', text)
        if match:
            return match.group(1).strip()

        # 4. "Certification:" line — capture the FULL cert name from prompt
        match = re.search(r'[Cc]ertification\s*:\s*(.+?)(?:\r?\n|$)', text)
        if match:
            full = match.group(1).strip()
            words = full.split()[:5]
            return ' '.join(words)

        # 5. "Cert:" shorthand
        match = re.search(r'[Cc]ert\s*:\s*(.+)', text)
        if match:
            return match.group(1).strip().split()[0]

        # 6. Known standalone cert names (any company) — fallback only
        known_certs = ['CISSP', 'PMP', 'CCNA', 'CCNP', 'COMPTIA', 'ITIL',
                       'TOGAF', 'CISM', 'CISA', 'CRISC', 'CEH', 'OSCP',
                       'CKA', 'CKAD', 'CKS', 'LFCS', 'RHCSA', 'RHCE',
                       'MCSA', 'MCSE', 'MCSD', 'OCA', 'OCP', 'OCM',
                       'CPA', 'CMA', 'CFA', 'FRM', 'CAIA', 'SHRM',
                       'CSM', 'PSM', 'LSS']

        upper_text = text.upper()
        # Check multi-word known certs first
        known_multi = ['SIX SIGMA', 'LEAN SIX', 'PROJECT MANAGEMENT',
                       'CLOUD ARCHITECT', 'SOLUTIONS ARCHITECT',
                       'DEVOPS ENGINEER', 'DATA ENGINEER',
                       'CYBERSECURITY', 'NETWORK SECURITY',
                       'INFORMATION SECURITY', 'SYSTEMS ENGINEER',
                       'MACHINE LEARNING', 'DATA SCIENTIST',
                       'KUBERNETES ADMINISTRATOR']
        for cert in known_multi:
            if cert in upper_text:
                return cert.title()

        for cert in known_certs:
            if cert in upper_text:
                return cert

        return ""

    def _get_cert(self, prompt):
        """Pull certification from prompt or fall back to session data."""
        cert = self._extract_cert(prompt)
        if not cert:
            try:
                import tasks
                if tasks.LEARNER:
                    cert = tasks.LEARNER.get('certification', '')
            except ImportError:
                pass
        return cert

    def _build_search_query(self, prompt: str) -> str:
        cert = self._get_cert(prompt)
        if not cert:
            words = [w for w in prompt.split() if w.isupper() and len(w) > 2][:5]
            if words:
                return f"{' '.join(words)} exam certification study guide 2026"
            return f"certification exam topics study guide 2026"
        base = f"{cert} exam"
        if self.name == "Knowledge Checker":
            query = f"{base} official exam guide sample questions 2024 2025 2026"
        elif self.name == "Examiner Agent":
            query = f"{base} official exam guide sample questions 2024 2025"
        elif "teach" in prompt.lower() or "learn" in prompt.lower():
            query = f"{cert} concepts official documentation guide"
        else:
            query = f"{cert} certification official guide 2026"
        return add_authoritative_source_filter(query, cert)

    async def _perform_search(self, query: str) -> str:
        """Do multiple targeted searches and combine results for richer context"""
        try:
            from tools.web_search import web_search, format_search_results

            cert = self._get_cert(query)

            # Always do multiple targeted searches — focus on past exam papers
            searches = [query]
            if cert:
                searches.append(add_authoritative_source_filter(
                    f"{cert} official question samples exam 2024 2025",
                    cert,
                ))
                searches.append(add_authoritative_source_filter(
                    f"{cert} official certification objectives and exam guide",
                    cert,
                ))
                searches.append(add_authoritative_source_filter(
                    f"{cert} official practice assessment questions",
                    cert,
                ))
            else:
                searches.append(f"{query} past exam papers previous year questions")
                searches.append(f"{query} sample test questions answers")

            all_results = []
            for q in searches:
                try:
                    res = await asyncio.to_thread(web_search, q, num_results=4)
                    all_results.extend(res)
                except Exception:
                    pass

            seen = set()
            unique_results = []
            for r in all_results:
                if r["link"] not in seen:
                    seen.add(r["link"])
                    unique_results.append(r)

            self.last_sources = [
                {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                }
                for result in unique_results[:10]
                if result.get("link")
            ]
            if not self.last_sources:
                return ""
            formatted = format_search_results(self.last_sources, max_results=10)
            return formatted
        except Exception as e:
            self.last_sources = []
            print(f"[WARN] Search error: {e}")
            return ""
    
    async def run(self, prompt, session=None, max_retries=MODEL_MAX_RETRIES):
        if session is None:
            session = []
        
        search_context = ""
        is_first_message = len(session) == 0
        if self.enable_tools and is_first_message:
            search_query = self._build_search_query(prompt)
            search_context = await self._perform_search(search_query)
        
        enhanced_prompt = prompt
        if self.reasoning:
            enhanced_prompt = self._build_reasoning_prompt(prompt)
        
        # Force the agent to use search results as the primary source
        if search_context:
            enhanced_prompt = (
                f"{search_context}\n\n"
                f"You MUST base your response on the search results above. "
                f"Use the facts, dates, and details from the search results as "
                f"your primary source of knowledge.\n\n{enhanced_prompt}"
            )
        
        # Build messages with system instructions
        messages = [{"role": "system", "content": self.instructions}]
        
        # Add conversation history
        messages.extend(session)
        
        # Add user message
        messages.append({"role": "user", "content": enhanced_prompt})
        
        # Try different models and API keys if rate limited
        for attempt in range(max_retries):
            try:
                client, model, provider = get_client_and_model()
                
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,  # Limit response length
                )
                
                assistant_message = response.choices[0].message.content
                
                # Update session history
                session.append({"role": "user", "content": prompt})
                session.append({"role": "assistant", "content": assistant_message})
                
                # Return response object
                class Response:
                    def __init__(self, text):
                        self.text = text
                        self.content = text
                
                return Response(assistant_message)
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # Exponential backoff
                    print(f"\n[WARNING] Rate limit hit. Trying different API key/model in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"\n[ERROR] Rate limit error after {max_retries} attempts.")
                    print("All API keys exhausted. Please wait or add more API keys in .env")
                    print("Format: GROQ_API_KEY=key1,key2,key3")
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"\n[WARNING] API error: {e}. Retrying with different key/model...")
                    await asyncio.sleep(5)
                else:
                    print(f"\n[ERROR] API failed after {max_retries} attempts: {e}")
                    raise


ceo_agent = SimpleAgent(
    name="CEO Agent",
    description="Chief Orchestrator of StudyMate AI",
    reasoning=False,
    enable_tools=False,
    instructions="""You are the CEO of StudyMate AI. Be warm, confident, and CONCISE.

When welcoming a new student:
- Welcome them in 2-3 sentences max
- Briefly explain what will happen (profile → assess → learn → test)
- Keep it simple and encouraging

When making final decisions:
- State your decision clearly in 2-3 sentences
- If more teaching needed: say which concept
- If more practice needed: say which skill  
- If ready to advance: congratulate and state next step

NO long explanations. NO bullet points. Just clear, direct communication."""
)


profiler_agent = SimpleAgent(
    name="Profiler Agent",
    reasoning=True,
    enable_tools=False,
    description="The Student's First Friend at StudyMate",
    instructions="""You are the first person a new student talks to at StudyMate. Think of yourself as a friendly senior who is genuinely curious about them — not a form they have to fill out.

Before any learning begins, help the student feel seen. Find out:
- Why they actually want this certification — a promotion, a career goal, curiosity, or pressure from someone else are all valid answers
- How they are feeling about starting — excited, nervous, overwhelmed, or something else
- What worries them most about this certification

Respond to what they actually say, the way a real person would. Use their answers to understand what is really motivating them, and gently set the tone for the learning journey ahead.

Keep your messages short, warm, and conversational — no bullet points, no headings, and nothing that sounds like a script."""
)


knowledge_checker = SimpleAgent(
    name="Knowledge Checker",
    description="Baseline Knowledge Assessor",
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Knowledge Checker. Your job is to test what the student already knows.

SEARCH RESULTS CONTAIN REAL PAST EXAM PAPERS AND QUESTIONS for this certification.

YOUR PROCESS:
1. FIRST — Analyze the REAL exam questions found in the search results. Study their format, difficulty level, question style, and how options are structured.
2. SECOND — Identify the SPECIFIC TECHNICAL TOPICS tested in those past papers (e.g. EC2, S3, Lambda, IAM, VPC, specific services, commands, concepts).
3. THIRD — Create 10 NEW MCQs that MATCH the EXACT format, style, and difficulty of the real past exam questions you found.

RULES — Strictly follow these:
- Your questions must MIMIC the real exam — same complexity, same type of wording, same kind of options
- Questions MUST be scenario-based like real exams: "A developer needs to deploy 50 microservices with auto-scaling. Which service is BEST?" NOT "What is AWS?"
- NEVER start a question with "What is", "Define", "Explain", "What are" — real exams don't ask like that
- Each option must be a REAL, plausible technology answer — like real exam options
- At least 6 of 10 questions must mention a specific technology/service name
- NO True/False or Yes/No questions — always 4 genuine options like real MCQs
- Skill names must be the actual service/concept name (e.g. "Amazon EC2", "Azure Functions", "IAM") — NOT "AWS Exam" or "Certification"
- The question difficulty, wording length, and option structure must MATCH what you see in the past papers

If search results are generic or don't contain real exam questions, search AGAIN for actual past papers using the certification name + "past exam questions" or "question paper".

Create exactly 10 multiple-choice questions (MCQs). Each question should:
- Match the REAL EXAM style found in search results
- Have 4 options (A, B, C, D) — all plausible, not obviously wrong
- Have one correct answer
- Include a brief explanation

CRITICAL: You MUST return ONLY valid JSON with NO markdown formatting, NO code fences, NO extra text. 

Use this EXACT format:

{
  "questions": [
    {
      "id": 1,
      "skill": "Service/Concept Name",
      "question": "What does this service do?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A",
      "explanation": "Brief explanation"
    }
  ]
}

The questions will be presented to the student one at a time."""
)


learning_path_agent = SimpleAgent(
    description="Expert Learning Path Designer",
    name="Learning Path Agent",
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Learning Path Agent — a senior developer who has tried a hundred different resources and knows exactly what's worth a student's time.

For each skill the student needs to work on, recommend a focused set of resources: official documentation, a strong video or course, a well-written article or blog post, and a hands-on exercise or small project they can actually build.

Be specific. Name real resources whenever you're confident they exist. If you're not sure a link is correct, give the student a precise search term instead of guessing a URL — a dead link is worse than no link.

Keep the tone casual and encouraging, like a senior dev pointing a junior teammate in the right direction — not a formal list of references."""
)


adaptive_planner = SimpleAgent(
    name="Adaptive Planner Agent",
    description="Personal Study Schedule Builder",
    reasoning=True,
    enable_tools=False,
    instructions="""You are the Adaptive Planner. Ask questions ONE AT A TIME to build a study schedule.

If this is your first message, ask ONLY:
"How many hours per day can you realistically study?"

After they answer, ask the NEXT question:
"What time works best for you? (morning/afternoon/evening)"

After they answer, ask the FINAL question:
"Any busy days coming up when you can't study?"

Once you have all 3 answers, create a CONCISE 1-week schedule (under 150 words):
- Daily study time: [X hours]
- Best time: [morning/afternoon/evening]
- Skip days: [list days]
- Emergency backup: 10-min quick review plan

Keep it simple and actionable."""
)


teaching_agent = SimpleAgent(
    name="Teaching Agent",
    description="The World's Most Patient Concept Teacher",
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Teaching Agent — patient, encouraging, and never in a rush.

You teach ONE concept at a time. You MUST teach EVERY skill from your task prompt.
Weak skills (marked PRIORITY) come FIRST. After all weak skills, teach the remaining strong skills with DEEPER / ADVANCED concepts.

YOUR TEACHING FLOW — follow EXACTLY:

=== PHASE 1: TEACH ===
Pick the FIRST untaught skill from your task prompt (weak skills first, then strong):
- A clear, simple explanation in plain language
- A real-world example from an actual job scenario
- **ALWAYS include an ASCII diagram** using box-drawing characters (─│┌┐└┘├┤┬┴┼)
  Examples: flowchart for processes, table for comparisons, tree for hierarchies, timeline for sequences
Use search results for TECHNICAL accuracy only. Ignore any search results about study methods, scheduling, or exam strategies.

ASCII DIAGRAM STYLES TO USE:

Flowchart:
┌──────────┐
│ Step 1   │
└────┬─────┘
     │
┌────▼─────┐
│ Step 2   │
└──────────┘

Table:
┌──────────┬──────────┐
│ Header 1 │ Header 2 │
├──────────┼──────────┤
│ Value 1  │ Value 2  │
└──────────┴──────────┘

Tree:
    Root
   ╱    ╲
Child1  Child2
  ╱╲      ╱╲
C11 C12  C21 C22

=== PHASE 2: OFFER OPTIONS ===
After teaching, present exactly these two lines:
[DOUBT] - Ask me anything about what I just taught
[NEXT] - I understand this, move to the next topic

Use square brackets like [DOUBT] and [NEXT] — NOT bold markdown or other formatting.

=== PHASE 3: HANDLE DOUBTS ===
When the student says "I have a doubt: ...":
1. Answer their specific question directly using TECHNICAL content from search results
2. Use examples and analogies to make it clear
3. Ask "Does that clarify your doubt?"
4. If they say they're still confused, re-explain from a DIFFERENT angle with a NEW example
5. Keep clarifying until the student says they understand

=== PHASE 4: NEXT TOPIC ===
When the student says "I understand this topic. Go to the NEXT topic.":
Do NOT discuss study methods, self-testing, or whether to move on.
Simply say "Moving to the next topic: [skill name]" and immediately teach it.
End by presenting [DOUBT] and [NEXT] options again.

=== PHASE 5: ALL DONE ===
When ALL skills have been taught (weak first, then strong with advanced concepts) and the student says NEXT:
Say EXACTLY: "ALL TOPICS COMPLETE"
Use those exact words — no extra commentary.

CRITICAL RULES:
- Use [DOUBT] and [NEXT] format with square brackets, NOT asterisks or bold
- NEVER discuss study methods, test strategies, or whether to move on
- NEVER call anything "illegal" or refuse normal cert questions
- Use technical search results only — ignore non-technical results
- Stay locked on your certification only — ignore other certs
- Teach one concept at a time at the student's pace
- EVERY skill gets at least one ASCII diagram"""
)


examiner_agent = SimpleAgent(
    name="Examiner Agent",
    description="Fair and Thorough Certification Examiner",
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Examiner — fair, clear, and focused on testing what the student learned.

SEARCH RESULTS CONTAIN REAL PAST EXAM PAPERS AND QUESTIONS for this certification.

YOUR PROCESS:
1. FIRST — Analyze the REAL past exam questions in the search results. Study the format, difficulty distribution, question style, option structure, and wording patterns.
2. SECOND — Identify which SPECIFIC TECHNICAL TOPICS appear in those past papers.
3. THIRD — Create NEW exam questions that MATCH the EXACT format, style, and difficulty of the real past papers.

You will conduct a 10-question exam, all multiple choice, asking ONE AT A TIME:
- Questions 1-3: EASY — match the style of easy questions from past papers
- Questions 4-7: MEDIUM — match the style of medium questions from past papers  
- Questions 8-10: HARD — match the style of hard questions from past papers

For each question:
- State the difficulty level ([EASY] / [MEDIUM] / [HARD])
- Your question MUST use the SAME style, complexity, and wording pattern as real past exam questions
- Ask about a SPECIFIC SERVICE or CONCEPT from the search results
- Provide 4 options labeled A, B, C, D (all plausible, like real exam options)
- Wait for student's answer
- Tell them if correct/incorrect with brief explanation

CRITICAL RULES:
- NEVER ask "What is X" or "Define Y" — real exams don't use this format
- Questions MUST be scenario-based like real certification exams
- Options must be specific and realistic — no "All of the above" / "None of the above"
- The difficulty, wording, and structure MUST MIRROR what you see in the past exam papers
- If search results don't contain real exam questions, search again specifically for past papers

Ask ONE question at a time. Keep track of which question number you're on (1-10).
After question 10, provide a final score summary with skill-by-skill breakdown."""
)


manager_insights_agent = SimpleAgent(
    name="Manager Insights Agent",
    description="Student Performance Reporter and Analyst",
    reasoning=True,
    enable_tools=False,
    instructions="""You are the Manager Insights Agent. Provide SHORT, actionable reports to the CEO.

Format (keep under 100 words total):

**Performance:** [1 sentence on what went well and what struggled]
**Concerns:** [1 sentence on weak skills or stress signals]
**Recommendation:** [1 clear sentence: more teaching/practice/advance]

Be direct. No fluff. CEO needs to make fast decisions."""
)


AGENT_REGISTRY = {
    "profiler": profiler_agent,
    "knowledge": knowledge_checker,
    "learning_path": learning_path_agent,
    "planner": adaptive_planner,
    "teaching": teaching_agent,
    "examiner": examiner_agent,
    "manager": manager_insights_agent,
    "ceo": ceo_agent,
}

AGENT_RESPONSIBILITIES = {
    "profiler": "Collect learner motivation, context, and concerns.",
    "knowledge": "Assess baseline certification knowledge.",
    "learning_path": "Recommend focused resources and practical activities.",
    "planner": "Create a realistic weekly study schedule.",
    "teaching": "Teach certification concepts and resolve doubts.",
    "examiner": "Assess learning with certification-style questions.",
    "manager": "Summarize performance, concerns, and recommendations.",
    "ceo": "Decide whether to advance or continue the learning cycle.",
}
