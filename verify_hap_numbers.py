"""
HAP Number Verification
=======================
Enforces the grounding rule mechanically: every numeric value in a generated
HAP draft must appear verbatim in the assembled data file the LLM was given
(<city>_hap_data.md). Numbers the LLM invented, derived, or mis-transcribed
are reported with their line numbers.

Usage:
    python3 verify_hap_numbers.py --draft agra_hap_draft.md --data agra_hap_data.md
Exit code 0 = all numbers grounded; 1 = violations found.
"""

import argparse
import re
import sys

NUM_RE = re.compile(r'\d[\d,]*(?:\.\d+)?')

# Numbers that legitimately appear in any HAP without being ward data:
# section numbers, list positions, and small enumeration counts.
STRUCTURAL_WHITELIST = {str(n) for n in range(0, 11)}


def extract(text):
    """Yield (line_no, token) for every number token, comma-stripped."""
    for i, line in enumerate(text.splitlines(), 1):
        for m in NUM_RE.finditer(line):
            yield i, m.group(0).replace(',', ''), line.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draft', required=True)
    ap.add_argument('--data', required=True)
    args = ap.parse_args()

    data_text = open(args.data).read()
    allowed = {tok for _, tok, _ in extract(data_text)}
    # Also allow the unrounded integer form of any allowed decimal (e.g. data
    # says "3.10" -> "3.1" in prose is the same number) and vice versa.
    normalized = set(allowed)
    for tok in allowed:
        if '.' in tok:
            normalized.add(tok.rstrip('0').rstrip('.'))
    allowed |= normalized

    draft_text = open(args.draft).read()
    # Template-mandated spans are exempt from grounding:
    #   [BLANK: ...]  — instructions to the human planner, not data claims
    #   [VERIFY: ...] — Tier B context facts (city demographics, heatwave
    #                   history, state policy) awaiting human confirmation;
    #                   the template requires every such number be wrapped,
    #                   so any Tier B number OUTSIDE a [VERIFY] still fails
    #   [MAP: ...]    — map-insertion placeholders
    draft_text = re.sub(r'\[(BLANK|VERIFY|MAP):.*?\]', r'[\1]', draft_text,
                        flags=re.DOTALL)
    violations = []
    checked = 0
    for line_no, tok, context in extract(draft_text):
        checked += 1
        t = tok
        if '.' in t:
            t_norm = t.rstrip('0').rstrip('.')
        else:
            t_norm = t
        if t in allowed or t_norm in allowed or t in STRUCTURAL_WHITELIST:
            continue
        # Subsection numbers in headings ("### 4.1 ...") are structure, not data
        if context.startswith('#') and re.fullmatch(r'\d{1,2}\.\d', tok):
            continue
        violations.append((line_no, tok, context))

    print(f'checked {checked} numeric tokens in {args.draft} '
          f'against {len(allowed)} grounded values in {args.data}')
    if violations:
        print(f'\n{len(violations)} UNGROUNDED numbers found:')
        for line_no, tok, context in violations:
            print(f'  line {line_no}: "{tok}"  in: {context[:100]}')
        sys.exit(1)
    print('OK — every number in the draft is grounded in the source data.')


if __name__ == '__main__':
    main()
