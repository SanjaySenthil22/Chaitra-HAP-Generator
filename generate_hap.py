"""
HAP Generator — one command from city name to verified Word document
====================================================================
Orchestrates the full chain:

  1. Ward data      (chaitra_ward_pipeline.py, run only if CSV missing)
  2. Prompt assembly (assemble_hap_prompt.py)
  3. LLM drafting    (Claude API — requires ANTHROPIC_API_KEY; web search
                      on by default so Tier B context sections can be
                      researched — disable with --no-web-search)
  4. Verification    (verify_hap_numbers.py; on failure, one retry where the
                      violations are fed back to the model to correct)
  5. Layer maps      (make_hap_maps.py — ward choropleths from GEE, inserted
                      at the [MAP: ...] placeholders; best-effort)
  6. Word conversion (pandoc)

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 generate_hap.py --city Agra --project <gcp-project>

The --project flag is only needed when step 1 has to run (no ward CSV yet).
"""

import argparse
import os
import subprocess
import sys

MODEL = 'claude-opus-4-8'
MAX_TOKENS = 32000


def run(cmd, **kw):
    print('$', ' '.join(cmd))
    return subprocess.run(cmd, **kw)


def call_claude(prompt_text, prior_messages=None, web_search=False):
    try:
        import anthropic
    except ImportError:
        sys.exit('The anthropic package is required: pip3 install anthropic')
    if not os.environ.get('ANTHROPIC_API_KEY'):
        sys.exit('Set ANTHROPIC_API_KEY first (console.anthropic.com).')

    client = anthropic.Anthropic()
    messages = (prior_messages or []) + [{'role': 'user', 'content': prompt_text}]
    kwargs = dict(model=MODEL, max_tokens=MAX_TOKENS, messages=messages)
    if web_search:
        # Server-side web search lets the model confirm Tier B context facts
        # (city heatwave statistics, state disaster notifications, schemes)
        # instead of relying on training knowledge. Facts still arrive
        # [VERIFY]-marked per the template; searches are billed per use.
        kwargs['tools'] = [{'type': 'web_search_20260209',
                            'name': 'web_search', 'max_uses': 8}]
    out = []
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            out.append(text)
    draft = ''.join(out)
    messages.append({'role': 'assistant', 'content': draft})
    return draft, messages


def main():
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='Agra')
    ap.add_argument('--project', default=os.environ.get('CHAITRA_GEE_PROJECT'),
                    help='GCP project with Earth Engine enabled — needed '
                         'only if ward data not yet computed (or set '
                         'CHAITRA_GEE_PROJECT)')
    ap.add_argument('--model', default=MODEL)
    ap.add_argument('--no-web-search', action='store_true',
                    help='Draft without web search (Tier B context sections '
                         'then rely on training knowledge only)')
    args = ap.parse_args()
    MODEL = args.model

    city, slug = args.city, args.city.lower()
    os.makedirs('outputs', exist_ok=True)
    py = sys.executable

    # 1. Ward data (skip if present)
    if not os.path.exists(f'outputs/{slug}_ward_data.csv'):
        if not args.project:
            sys.exit(f'No outputs/{slug}_ward_data.csv — pass --project to compute it.')
        r = run([py, 'chaitra_ward_pipeline.py', '--city', city, '--project', args.project])
        if r.returncode:
            sys.exit('Pipeline failed.')

    # 2. Assemble prompt
    r = run([py, 'assemble_hap_prompt.py', '--city', city])
    if r.returncode:
        sys.exit('Prompt assembly failed.')

    # 3. Draft via Claude
    prompt = open(f'outputs/{slug}_hap_prompt.md').read()
    use_search = not args.no_web_search
    print(f'Calling {MODEL} to draft the HAP (streaming'
          f'{", web search enabled" if use_search else ""})...')
    draft, messages = call_claude(prompt, web_search=use_search)
    draft_path = f'outputs/{slug}_hap_draft.md'
    open(draft_path, 'w').write(draft)
    print(f'wrote {draft_path} ({len(draft):,} chars)')

    # 4. Verify; one corrective retry on failure
    data_path = f'outputs/{slug}_hap_data.md'
    for attempt in (1, 2):
        r = run([py, 'verify_hap_numbers.py', '--draft', draft_path,
                 '--data', data_path], capture_output=True, text=True)
        print(r.stdout)
        if r.returncode == 0:
            break
        if attempt == 2:
            sys.exit('Draft still contains ungrounded numbers after retry — '
                     'human review required. Violations above.')
        print('Verification failed — asking the model to correct...')
        fix_request = (
            'Your draft contains numbers that do not appear in the WARD DATA. '
            'The automated verifier reported:\n\n' + r.stdout +
            '\nRewrite the COMPLETE document, correcting these values so that '
            'every number is copied exactly from the WARD DATA (or removed if '
            'it cannot be grounded). Output the full corrected document only.')
        draft, messages = call_claude(fix_request, messages)
        open(draft_path, 'w').write(draft)

    # 5. Layer maps (best-effort: needs the authenticated GEE account;
    #    on failure the [MAP: ...] placeholders stay in the draft)
    map_cmd = [py, 'make_hap_maps.py', '--city', city, '--insert']
    if args.project:
        map_cmd += ['--project', args.project]
    r = run(map_cmd)
    if r.returncode:
        print('WARNING: map rendering failed — draft keeps [MAP] placeholders.')

    # 6. Word document (render step converts [VERIFY]/[BLANK] markup to the
    #    reader-facing asterisk + "To be completed by city officials" style)
    r = run([py, 'render_hap_docx.py', '--city', city])
    if r.returncode:
        sys.exit('Render/pandoc step failed.')
    print(f'\nDone: outputs/{city}_HAP_Draft.docx (verified draft: {draft_path})')


if __name__ == '__main__':
    main()
