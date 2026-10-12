"""Conservative HTML section extraction and exact paragraph evidence."""
import re
from difflib import SequenceMatcher
from bs4 import BeautifulSoup

HEADING = re.compile(r"^item\s+(1a|1b|1c|1|2)\s*[. :–—-]*\s*(.*)$", re.I)
TITLES = {'1': 'business', '1a': 'risk factors', '1b': 'unresolved staff comments',
          '1c': 'cybersecurity', '2': 'properties'}

def extract_sections(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'ix:header']):
        tag.decompose()
    # Preserve paragraph boundaries but keep inline formatting on the same line.
    for tag in soup.find_all(['p', 'div', 'tr', 'h1', 'h2', 'h3', 'h4', 'br']):
        tag.insert_before('\n')
        tag.insert_after('\n')
    lines = [re.sub(r'\s+', ' ', s).strip() for s in soup.get_text().splitlines()]
    lines = [s for s in lines if s]
    headings = []
    for i, line in enumerate(lines):
        match = HEADING.match(line)
        if not match:
            continue
        item, title = match.groups()
        item = item.lower()
        title = title.lower().strip()
        if not title and i + 1 < len(lines):
            title = lines[i + 1].lower()
        if title.startswith(TITLES[item]) and len(line) < 160:
            headings.append((i, item))
    sections = {}
    for item, boundary in [('1', '1a'), ('1a', '1b')]:
        candidates = []
        for start, found in headings:
            if found != item:
                continue
            ends = [end for end, next_item in headings if end > start and
                    (next_item == boundary or (item == '1a' and next_item in ('1c', '2')))]
            if ends:
                body = lines[start + 1:min(ends)]
                body = [s for s in body if s.lower() != TITLES[item]]
                candidates.append(body)
        if not candidates:
            raise ValueError(f'Cannot confidently locate Item {item.upper()} and its ending heading.')
        # TOCs have short spans; choose the largest complete section, never a tail to EOF.
        body = max(candidates, key=lambda p: sum(map(len, p)))
        if sum(map(len, body)) < 100:
            raise ValueError(f'Item {item.upper()} is too short to trust.')
        sections[item] = body
    return sections

def compare(before: list[str], after: list[str]) -> list[dict]:
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip().casefold()
    matcher = SequenceMatcher(None, list(map(normalize, before)), list(map(normalize, after)), autojunk=False)
    changes = []
    for kind, i, j, a, b in matcher.get_opcodes():
        if kind == 'equal':
            continue
        changes.append({'kind': kind, 'before': [{'paragraph': n + 1, 'text': before[n]} for n in range(i, j)],
                        'after': [{'paragraph': n + 1, 'text': after[n]} for n in range(a, b)]})
    return changes
