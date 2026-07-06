"""
agents.py — StudyMate AI Agent Definitions (Direct Groq Integration)

Enhanced agent implementation with verbose/debug, reasoning, and Foundry IQ search.
"""

from openai import AsyncOpenAI, RateLimitError
from dotenv import load_dotenv
import os
import asyncio
import random
import re
import time
from datetime import datetime

load_dotenv()

# Multiple API keys for rotation
API_KEYS = []

# Collect all GROQ_API_KEY* environment variables
for key in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GROQ_API_KEY_5"]:
    api_key = os.getenv(key)
    if api_key and api_key.strip():
        API_KEYS.append(api_key.strip())

# Also support comma-separated keys in GROQ_API_KEY
if os.getenv("GROQ_API_KEY"):
    for key in os.getenv("GROQ_API_KEY", "").split(","):
        if key.strip() and key.strip() not in API_KEYS:
            API_KEYS.append(key.strip())

if not API_KEYS:
    raise ValueError("No GROQ_API_KEY found in .env file!")

print(f"[API] Loaded {len(API_KEYS)} API key(s) for rotation")

# Multiple models for load balancing and rate limit handling
# Using stable models without tool-calling issues
MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile"
]

def get_groq_client():
    """Get a Groq client with a random API key"""
    api_key = random.choice(API_KEYS)
    return AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

def get_model():
    """Rotate between available models to handle rate limits"""
    return random.choice(MODELS)


def print_debug(message: str, verbose: bool = False):
    """Print debug messages when verbose mode is enabled"""
    if verbose:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}")


def print_reasoning(step: int, thought: str, verbose: bool = False):
    """Print reasoning steps when verbose mode is enabled"""
    if verbose:
        print(f"[REASONING Step {step}] {thought}")


class SimpleAgent:
    def __init__(self, name, description, instructions, verbose=False, reasoning=False, enable_tools=False):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.verbose = verbose
        self.reasoning = reasoning
        self.enable_tools = enable_tools
        self.tool_calls_count = 0
        self.total_tokens = 0
        
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

    def _build_search_query(self, prompt: str) -> str:
        cert = self._extract_cert(prompt)
        if not cert:
            # Try to get cert from LEARNER data (always more reliable)
            try:
                import tasks
                if tasks.LEARNER and tasks.LEARNER.get('certification'):
                    cert = tasks.LEARNER['certification']
            except ImportError:
                pass
        if not cert:
            # Ultra fallback: extract key terms from prompt
            words = [w for w in prompt.split() if w.isupper() and len(w) > 2][:5]
            if words:
                return f"{' '.join(words)} exam certification study guide 2026"
            return f"certification exam topics study guide 2026"
        base = f"{cert} 2026"
        if self.name == "Knowledge Checker":
            return f"{base} exam topics skills breakdown practice questions"
        elif self.name == "Examiner Agent":
            return f"{base} real exam questions practice test sample questions"
        elif "teach" in prompt.lower() or "learn" in prompt.lower():
            return f"{base} concepts tutorial documentation guide"
        else:
            return f"{base} latest updates certification guide"

    async def _perform_search(self, query: str) -> str:
        """Do multiple targeted searches and combine results for richer context"""
        try:
            from tools.web_search import web_search, format_search_results

            cert = self._extract_cert(query)
            if not cert:
                try:
                    import tasks
                    if tasks.LEARNER and tasks.LEARNER.get('certification'):
                        cert = tasks.LEARNER['certification']
                except ImportError:
                    pass

            # Always do multiple targeted searches
            searches = [query]
            if cert:
                searches.append(f"{cert} exam topics skills breakdown")
                searches.append(f"{cert} study guide real questions")
            else:
                # For unknown certs, search from multiple angles
                searches.append(f"{query} concepts topics overview")
                searches.append(f"{query} study guide practice questions")

            all_results = []
            for q in searches:
                try:
                    res = web_search(q, num_results=4)
                    all_results.extend(res)
                except:
                    pass

            seen = set()
            unique_results = []
            for r in all_results:
                if r["link"] not in seen:
                    seen.add(r["link"])
                    unique_results.append(r)

            formatted = format_search_results(unique_results[:10], max_results=10)
            self.tool_calls_count += 1

            if self.verbose:
                print(f"\n[TOOL CALL] web_search ({len(searches)} queries, {len(unique_results)} unique results)")
                for i, q in enumerate(searches):
                    print(f"[QUERY {i+1}] {q}")
                print(formatted)

            return formatted
        except Exception as e:
            print_debug(f"Search error: {e}", self.verbose)
            return ""
    
    async def run(self, prompt, session=None, max_retries=3):
        """Run the agent with a prompt, with rate limit handling"""
        start_time = time.time()
        
        if session is None:
            session = []
        
        # Verbose mode: Show input details
        if self.verbose:
            print("\n" + "="*70)
            print(f"[AGENT] {self.name}")
            print(f"[INPUT] {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"[SESSION] {len(session)} messages in history")
            # print(f"[DEBUG] Full prompt: {prompt[:200]}...")  # sometimes useful for debugging
        
        # Build targeted search query and fetch latest information
        # Only search on the FIRST message in a session to avoid derailing
        # follow-up messages (like "yes", "next") with irrelevant search results
        search_context = ""
        is_first_message = session is None or len(session) == 0
        if self.enable_tools and is_first_message:
            search_query = self._build_search_query(prompt)
            print_debug(f"Searching web for: {search_query}", self.verbose)
            search_context = await self._perform_search(search_query)
        elif self.enable_tools:
            print_debug("Skipping web search (follow-up message in session)", self.verbose)
        
        # Build enhanced prompt with reasoning if enabled
        enhanced_prompt = prompt
        if self.reasoning:
            enhanced_prompt = self._build_reasoning_prompt(prompt)
            print_debug("Chain-of-Thought reasoning enabled", self.verbose)
        
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
                groq_client = get_groq_client()
                model = get_model()
                
                print_debug(f"Using model: {model}", self.verbose)
                
                # Avoid tool-capable models if they cause issues
                if model == "openai/gpt-oss-20b":
                    model = "llama-3.1-8b-instant"  # Fallback to stable model
                
                response = await groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,  # Limit response length
                )
                
                assistant_message = response.choices[0].message.content
                
                # Track token usage (approximate)
                prompt_tokens = sum(len(m.get("content", "")) for m in messages) // 4
                completion_tokens = len(assistant_message) // 4
                self.total_tokens += (prompt_tokens + completion_tokens)
                
                # Update session history
                session.append({"role": "user", "content": prompt})
                session.append({"role": "assistant", "content": assistant_message})
                
                # Verbose mode: Show output details
                elapsed = time.time() - start_time
                if self.verbose:
                    print(f"[MODEL] {model}")
                    print(f"[TOKENS] ~{prompt_tokens} prompt + ~{completion_tokens} completion = ~{prompt_tokens + completion_tokens} total")
                    print(f"[TIME] {elapsed:.2f}s")
                    print(f"[TOOLS USED] {self.tool_calls_count} calls this session")
                    print(f"[OUTPUT LENGTH] {len(assistant_message)} characters")
                    print("="*70 + "\n")
                
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


ceo_agent = SimpleAgent(
    name="CEO Agent",
    description="Chief Orchestrator of StudyMate AI",
    verbose=False,
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
    verbose=False,
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
    verbose=False,
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Knowledge Checker. Your job is to test what the student already knows.

SEARCH RESULTS ARE PROVIDED ABOVE. They contain certification topics, exam domains, services, and concepts for this exam.

YOUR TASK:
1. SCAN the search results for SPECIFIC TECHNICAL TOPICS — services (e.g. EC2, S3, Lambda, Azure Functions), concepts (e.g. IAM, VPC, Blob Storage), and architectural patterns
2. Create 10 MCQs that test knowledge of those SPECIFIC TECHNICAL TOPICS
3. Each question must be about a concrete technology, service, or concept mentioned in the search results — NOT about the exam itself, study guides, or certification process
4. Skill names must be the actual service/concept name (e.g. "Amazon EC2", "Azure Functions", "IAM") — NOT "AWS Exam" or "Certification"

QUALITY RULES — Strictly follow these:
- Questions MUST be scenario-based: "A developer needs to deploy 50 microservices with auto-scaling. Which service is BEST?" NOT "What is AWS?"
- NEVER start a question with "What is", "Define", "Explain", "What are" — these are vague
- Each option must be a REAL, plausible technology answer — not obviously wrong
- Prefer questions about specific features, limitations, or comparisons
- If search results are generic, search MORE SPECIFICALLY: look for actual exam dumps, skill breakdowns, and service documentation
- At least 6 of 10 questions must mention a specific technology/service name
- NO True/False or Yes/No questions — always 4 genuine options

Create exactly 10 multiple-choice questions (MCQs). Each question should:
- Test a SPECIFIC SERVICE or CONCEPT found in the search results
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
    verbose=False,
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
    verbose=False,
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
    verbose=False,
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Teaching Agent — patient, encouraging, and never in a rush.

You teach ONE concept at a time. Each teaching session covers the weak skill areas listed in your task prompt.

YOUR TEACHING FLOW — follow EXACTLY:

=== PHASE 1: TEACH ===
Pick the FIRST untaught weak skill from your task prompt and teach it:
- A clear, simple explanation in plain language
- A real-world example from an actual job scenario
Use search results for TECHNICAL accuracy only. Ignore any search results about study methods, scheduling, or exam strategies.

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
When ALL weak skills have been taught and the student says NEXT:
Say EXACTLY: "ALL TOPICS COMPLETE"
Use those exact words — no extra commentary.

CRITICAL RULES:
- Use [DOUBT] and [NEXT] format with square brackets, NOT asterisks or bold
- NEVER discuss study methods, test strategies, or whether to move on
- NEVER call anything "illegal" or refuse normal cert questions
- Use technical search results only — ignore non-technical results
- Stay locked on your certification only — ignore other certs
- Teach one concept at a time at the student's pace"""
)


examiner_agent = SimpleAgent(
    name="Examiner Agent",
    description="Fair and Thorough Certification Examiner",
    verbose=False,
    reasoning=True,
    enable_tools=True,
    instructions="""You are the Examiner — fair, clear, and focused on testing what the student learned.

SEARCH RESULTS ARE PROVIDED ABOVE. They contain real exam topics, services, and concepts for this certification.

YOUR TASK:
1. SCAN search results for SPECIFIC TECHNICAL TOPICS — actual services, tools, concepts, and architectures
2. Create 15 questions that test knowledge of those SPECIFIC TECHNICAL TOPICS
3. Questions must be about CONCRETE TECHNOLOGIES (e.g. EC2, S3, Lambda, VPC, IAM, Azure Functions, Blob Storage) — NOT about the exam format, study guides, or certification process

You will conduct a 15-question exam by asking questions ONE AT A TIME:
- Questions 1-5: EASY multiple choice — basic knowledge of services found in search results
- Questions 6-10: MEDIUM multiple choice — deeper concepts from search results
- Questions 11-15: HARD open-ended — real-world scenarios using services from search results

For each MCQ:
- State the difficulty level ([EASY] / [MEDIUM] / [HARD])
- Ask about a SPECIFIC SERVICE or CONCEPT from the search results
- Provide 4 options labeled A, B, C, D
- Wait for student's answer
- Tell them if correct/incorrect
- Give brief explanation

For open-ended questions:
- State it's a detailed question
- Ask about a real scenario using services found in search results
- Wait for their answer
- Provide detailed feedback

Ask ONE question at a time. Keep track of which question number you're on (1-15).
After question 15, provide a final score summary with skill-by-skill breakdown."""
)


manager_insights_agent = SimpleAgent(
    name="Manager Insights Agent",
    description="Student Performance Reporter and Analyst",
    verbose=False,
    reasoning=True,
    enable_tools=False,
    instructions="""You are the Manager Insights Agent. Provide SHORT, actionable reports to the CEO.

Format (keep under 100 words total):

**Performance:** [1 sentence on what went well and what struggled]
**Concerns:** [1 sentence on weak skills or stress signals]
**Recommendation:** [1 clear sentence: more teaching/practice/advance]

Be direct. No fluff. CEO needs to make fast decisions."""
)


# TODO: might want to add retry logic for tool failures
# TODO: consider adding caching for repeated Foundry IQ searches
