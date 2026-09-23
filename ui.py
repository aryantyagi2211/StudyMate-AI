"""
ui.py — Pixel-style terminal UI for StudyMate AI
Uses only ASCII-safe characters for maximum terminal compatibility.
Auto-detects ANSI color support with graceful fallback.
"""

import os
import shutil
import sys
import re

_USE_COLOR = True

def _init_ansi():
    global _USE_COLOR
    if os.name == 'nt':
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            mode = ctypes.c_uint32()
            h = k32.GetStdHandle(-11)
            if h and k32.GetConsoleMode(h, ctypes.byref(mode)):
                k32.SetConsoleMode(h, mode.value | 0x0004)
        except Exception:
            pass
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if not sys.stdout.isatty():
        _USE_COLOR = False

_init_ansi()

# ── Color palette ──────────────────────────────────────────────────────────
class C:
    RST = '\033[0m'
    BLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GRN = '\033[92m'
    YLW = '\033[93m'
    BLU = '\033[94m'
    MGT = '\033[95m'
    CYN = '\033[96m'
    WHT = '\033[97m'
    GRY = '\033[90m'

    # Background
    BG_RED = '\033[101m'
    BG_GRN = '\033[102m'
    BG_YLW = '\033[103m'
    BG_BLU = '\033[104m'
    BG_MGT = '\033[105m'
    BG_CYN = '\033[106m'

    @staticmethod
    def rgb(r, g, b):
        return f'\033[38;2;{r};{g};{b}m'

    @staticmethod
    def bg_rgb(r, g, b):
        return f'\033[48;2;{r};{g};{b}m'


# ── Box drawing (ASCII-safe) ──────────────────────────────────────────────
H = '='
V = '|'
TL = '.'
TR = '.'
BL = "'"
BR = "'"
LT = '|'
RT = '|'
DH = '='
DV = '|'
DTL = '.'
DTR = '.'
DBL = "'"
DBR = "'"
DLT = '|'
DRT = '|'

BLOCK = '#'
SHADE_L = '.'
TRI_R = '>'
DOT = '.'


_ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def strip_ansi(text):
    return _ANSI_RE.sub('', text)


def c(text, color):
    """Colorize text — falls back to plain text if ANSI not supported"""
    if not _USE_COLOR:
        return strip_ansi(text)
    return f'{color}{text}{C.RST}'


def bold(text):
    if not _USE_COLOR:
        return text.upper()
    return f'{C.BLD}{text}{C.RST}'


def terminal_width(default=60, minimum=24):
    """Return a usable content width for both wide and narrow terminals."""
    columns = shutil.get_terminal_size(fallback=(default + 4, 24)).columns
    return max(minimum, min(default, columns - 4))


# ── Headers ────────────────────────────────────────────────────────────────

def header(title, width=None):
    """Pixel-style header with double lines"""
    width = terminal_width(width or 60)
    title = title[: max(1, width - 2)]
    pad = width - len(title) - 2
    lpad = pad // 2
    rpad = pad - lpad
    line = f'{DTL}{DH * width}{DTR}'
    print()
    print(c(line, C.CYN))
    print(c(f'{DV}{" " * lpad}{C.BLD}{title}{C.RST}{" " * rpad}{DV}', C.CYN))
    print(c(f'{DBL}{DH * width}{DBR}', C.CYN))
    print()


def section(title):
    """Inline section marker"""
    print()
    print(c(f'  {c(TRI_R, C.CYN)} {bold(title)}', C.WHT))


# ── Boxes ──────────────────────────────────────────────────────────────────

def result_box(text, width=None):
    """Result box with colored borders"""
    width = terminal_width(width or 58)
    if not text:
        text = ""
    lines = text.split('\n')
    content_w = width - 4
    print(c(f'  {DTL}{DH * width}{DTR}', C.GRN))
    for line in lines:
        while len(line) > content_w:
            print(c(f'  {DV} {line[:content_w]} {DV}', C.GRN))
            line = line[content_w:]
        pad = content_w - len(line)
        print(c(f'  {DV} {line}{" " * pad} {DV}', C.GRN))
    print(c(f'  {DBL}{DH * width}{DBR}', C.GRN))


# ── Progress bar ────────────────────────────────────────────────────────────

def progress_bar(value, total, width=20, color=C.GRN):
    """Draw a pixel progress bar"""
    pct = value / total if total > 0 else 0
    filled = int(pct * width)
    empty = width - filled
    bar = f'{c(BLOCK * filled, color)}{c(SHADE_L * empty, C.GRY)}'
    pct_text = f'{int(pct * 100)}%'
    return f'{c("[", C.GRY)}{bar}{c("]", C.GRY)} {c(pct_text, C.BLD)}'


def score_display(correct, total, label="Score"):
    """Display score with progress bar"""
    pct = int((correct / total) * 100) if total > 0 else 0
    if pct >= 80:
        col = C.GRN
    elif pct >= 60:
        col = C.YLW
    else:
        col = C.RED
    bar = progress_bar(correct, total, 15, col)
    print(f'    {c(f"{label}:", C.WHT)} {bar}  {c(f"{correct}/{total}", C.BLD)}')
    return pct


def adaptive_cycle_status(cycle, max_cycles, score, weak_skills):
    """Show the current adaptive cycle and the stages it will execute."""
    weak_text = ", ".join(weak_skills) if weak_skills else "None identified"
    print(
        f"  {c('ADAPTIVE LOOP', C.CYN)}  "
        f"Cycle {cycle}/{max_cycles}  |  Current mastery: {score}%"
    )
    print(f"    {c('Teaching -> Examiner -> Manager -> CEO', C.WHT)}")
    print(f"    Weak skills: {c(weak_text, C.YLW if weak_skills else C.GRN)}")


def report_card(report):
    """Display the final outcome of the adaptive learning loop."""
    status_color = C.GRN if report["status"] == "MASTERED" else C.YLW
    weak_text = ", ".join(report["weak_skills"]) if report["weak_skills"] else "None"
    header("FINAL REPORT CARD")
    print(f"    Status: {c(report['status'], status_color + C.BLD)}")
    print(
        f"    Mastery: {c(str(report['score']) + '%', status_color + C.BLD)} "
        f"(required: {report['mastery_threshold']}%)"
    )
    print(f"    Learning cycles: {report['cycles']}")
    print(f"    Weak skills: {weak_text}")


# ── Options menu ───────────────────────────────────────────────────────────

def option_list(options):
    """Display a styled list of options"""
    for key, desc in options:
        print(f'    {c(f"[{key}]", C.CYN)}  {c(desc, C.WHT)}')


def input_prompt(text):
    """Styled input prompt. Gracefully handles Ctrl+C and EOF."""
    try:
        return input(f'  {c(TRI_R, C.CYN)} {c(text, C.BLD)} ')
    except (EOFError, KeyboardInterrupt):
        print()
        print(f'  {c("[!]", C.YLW)} Session interrupted. Goodbye!')
        sys.exit(0)


# ── Status indicators ──────────────────────────────────────────────────────

def ok(text):
    print(f'    {c("[OK]", C.GRN)} {text}')


def warn(text):
    print(f'    {c("[!]", C.YLW)} {text}')


def fail(text):
    print(f'    {c("[X]", C.RED)} {text}')


def info(text):
    print(f'    {c(DOT, C.CYN)} {c(text, C.GRY)}')


# ── Agent output display ───────────────────────────────────────────────────

def agent_output(agent_name, text, width=58):
    """Display agent output in a styled box"""
    width = terminal_width(width)
    content_w = width - 4
    print(c(f'  {DLT}{DH * width}{DRT}', C.MGT))
    # Agent name header
    name_line = f'{DV} {c(bold(agent_name), C.MGT)}'
    pad = width - len(agent_name) - 3
    name_line += c(f'{" " * pad}{DV}', C.MGT)
    print(name_line)
    print(c(f'  {LT}{H * width}{RT}', C.GRY))

    lines = text.split('\n')
    for line in lines:
        while len(line) > content_w:
            print(c(f'  {V} ', C.GRY) + line[:content_w] + c(f' {V}', C.GRY))
            line = line[content_w:]
        pad = content_w - len(line)
        print(c(f'  {V} ', C.GRY) + line + c(f'{" " * pad} {V}', C.GRY))
    print(c(f'  {BL}{H * width}{BR}', C.GRY))


# ── Question display ───────────────────────────────────────────────────────

def display_question(q_num, skill, question, options):
    """Display a question in pixel style"""
    width = terminal_width(56)
    content_w = width - 4
    print(c(f'  {DTL}{DH * width}{DTR}', C.CYN))
    skill_text = skill[: max(1, content_w - len(str(q_num)) - 5)]
    print(c(f'  {DV}  {c(f"Q{q_num}", C.YLW)}  {c(skill_text, C.BLD)}{" " * max(0, content_w - len(skill_text) - len(str(q_num)) - 4)}{DV}', C.CYN))
    print(c(f'  {LT}{H * width}{RT}', C.GRY))

    # Wrap question text
    q_words = question.split()
    q_lines = []
    current = ""
    for w in q_words:
        if len(current) + len(w) + 1 > content_w:
            q_lines.append(current)
            current = w
        else:
            current = (current + " " + w).strip()
    if current:
        q_lines.append(current)

    for line in q_lines:
        print(c(f'  {V} ', C.GRY) + line + c(f'{" " * max(0, content_w + 2 - len(line))} {V}', C.GRY))

    print(c(f'  {LT}{H * width}{RT}', C.GRY))

    for i, opt in enumerate(options):
        letter = chr(65 + i)
        option = str(opt)
        print(c(f'  {V}  ', C.GRY) + c(f'{letter}.', C.CYN) + c(f' {option}', C.WHT) + c(f'{" " * max(0, content_w - len(option) - 2)} {V}', C.GRY))

    print(c(f'  {BL}{H * width}{BR}', C.GRY))


def teaching_options():
    """Display teaching flow options"""
    width = terminal_width(56)
    content_w = width - 2
    print()
    print(c(f'  .{"=" * width}.', C.MGT))
    print(c(f'  |  {c(bold("TEACHING OPTIONS"), C.YLW)}{" " * max(0, content_w - len("  TEACHING OPTIONS"))} |', C.MGT))
    print(c(f'  +{"=" * width}+', C.MGT))
    print(c(f'  |  {c("[doubt]", C.CYN)}  {c("I have a doubt / question about this topic", C.WHT)} |', C.MGT))
    print(c(f'  |  {c("[next]", C.CYN)}   {c("I understand, move to the next topic", C.WHT)} |', C.MGT))
    print(c(f"  '{'=' * width}'", C.MGT))
    print()


# ── Loading animation ─────────────────────────────────────────────────────

async def start_loader(message):
    """Show an animated pixel loader while an agent works.
    Returns (task, stop_event) — call stop_event.set() then await task to finish.
    
    Usage:
        task, stop = await start_loader("Generating questions...")
        try:
            result = await agent.run(...)
        finally:
            stop.set()
            await task
    """
    import asyncio
    frames = ['#    ', '##   ', '###  ', ' ##  ', '  #  ', ' ##  ', '###  ']
    stop = asyncio.Event()

    async def _spin():
        i = 0
        while not stop.is_set():
            bar = frames[i % len(frames)]
            sys.stdout.write(f'\r  {c(bar, C.CYN)} {c(message, C.GRY)}')
            sys.stdout.flush()
            i += 1
            await asyncio.sleep(0.12)
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(message) + 12) + '\r')
        sys.stdout.flush()

    task = asyncio.create_task(_spin())
    return task, stop


# ── Learning Path display ─────────────────────────────────────────────────

_URL_RE = re.compile(r'(https?://[^\s)]+)')
_HEADER_RE = re.compile(r'\*\*(.+?)\*\*')
_BOLD_SKILL_RE = re.compile(r'^\s*\*\*(.+?)\*\*\s*$', re.MULTILINE)
_HASH_SKILL_RE = re.compile(r'^##\s+(.+)$', re.MULTILINE)

# Color palette for skill sections (cycles through them)
_SKILL_COLORS = [C.CYN, C.GRN, C.YLW, C.MGT, C.BLU, C.GRN]


def display_learning_path(text):
    """Display learning path content inside a pixel-style outer box,
    with colored skill sections, bullet markers, and highlighted links."""
    width = terminal_width(58)
    color_idx = 0

    # Split by skill-level headers (standalone **Header** or ## Header)
    header_positions = []
    for m in _BOLD_SKILL_RE.finditer(text):
        header_positions.append((m.start(), m.end(), m.group(1)))
    for m in _HASH_SKILL_RE.finditer(text):
        header_positions.append((m.start(), m.end(), m.group(1)))
    header_positions.sort()

    if not header_positions:
        # No sections found — fallback to rich lines inside a plain box
        _print_rich_lines(text.split('\n'))
        return

    sections = []
    for i, (start, end, hdr) in enumerate(header_positions):
        next_start = header_positions[i + 1][0] if i + 1 < len(header_positions) else len(text)
        body = text[end:next_start].strip()
        sections.append((hdr, body))

    # ── Outer pixel box ──
    header_text_mid = " LEARNING PATH "
    header_pad = width - len(header_text_mid) + 2
    lpad = header_pad // 2
    rpad = header_pad - lpad
    print(c(f'  .{"=" * width}.', C.MGT))
    print(c(f'  |{" " * lpad}{c(header_text_mid, C.YLW + C.BLD)}{" " * rpad}|', C.MGT))
    print(c(f'  |{"=" * (width + 2)}|', C.MGT))

    for idx, (header_text, body) in enumerate(sections):
        section_color = _SKILL_COLORS[color_idx % len(_SKILL_COLORS)]
        color_idx += 1
        header_upper = header_text.upper()

        # Skill header line with its own color
        hdr_line = f'  |{c(f"  [{idx + 1}] {header_upper} ", section_color + C.BLD):<{width + 2}s}|'
        print(c(hdr_line, section_color))
        print(c(f'  |{c("-" * (width + 2), C.DIM)}|', C.GRY))

        # Content lines
        lines = body.split('\n') if body else []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            display_line = _format_rich_line(line)
            if _USE_COLOR:
                plain_len = len(strip_ansi(display_line))
                padding = max(0, width - plain_len - 1)
                print(c(f'  | {display_line}{" " * padding} |', C.GRY))
            else:
                plain = strip_ansi(display_line)
                padding = max(0, width - len(plain) - 1)
                print(f'  | {plain}{" " * padding} |')

        if idx < len(sections) - 1:
            print(c(f'  |{c(" " * (width + 2), C.DIM)}|', C.GRY))

    print(c(f"  '{'=' * width}'", C.MGT))
    print()


def _format_rich_line(line):
    """Apply colors to URLs, bold text, and bullet markers in a line."""
    # Replace markdown bold markers with ANSI bold (or just text if no color)
    line = _HEADER_RE.sub(lambda m: bold(m.group(1)), line)

    # Color URLs
    line = _URL_RE.sub(lambda m: c(m.group(1), C.CYN), line)

    # Bullet markers
    if line.startswith('* ') or line.startswith('- '):
        bullet = c('>', C.YLW) if _USE_COLOR else '>'
        line = bullet + ' ' + line[2:]

    return line


def _print_rich_lines(lines):
    """Fallback: display lines with link highlighting"""
    for line in lines:
        display_line = _format_rich_line(line)
        if _USE_COLOR:
            print(f'  {display_line}')
        else:
            print(f'  {strip_ansi(display_line)}')


# ── Separator ──────────────────────────────────────────────────────────────

def separator(char='═', color=C.GRY):
    print(c(f'  {char * 58}', color))
