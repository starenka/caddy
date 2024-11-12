import collections
import glob
import logging
import traceback
from pathlib import Path

import requests
from art import text2art

from .challenges import CHALLENGES
from .utils import get_js_functions, get_py_functions, hprint, test_js, test_py

log = logging.getLogger(__name__)

SERVER = 'https://starenka:mola@mbgolf.starenka.net'
LANGS = {
    'JavaScript': {
        'ext': 'js', 'discover': get_js_functions, 'test': test_js,
        'template': '''/*

Write your challenge attempts here as functions. Any function with a name starting with
`{code}` will be tested and eventually submitted. If the challenge relies on input, the
input will be passed to your function as `s`. All chalanges expect the results to be
printed to stdout. Your code will be tested against Node.js 22.x on a Linux machine.

Run `make test` to test your solutions and `make submit` to submit them. Have fun.



Challange "{code}":
{name}

{desc}

*/


function {code}a(s) {{console.log()}}
'''},
    'Python': {
        'ext': 'py', 'discover': get_py_functions, 'test': test_py,
        'template': """r'''

Write your challenge attempts here as functions. Any function with a name starting with
`{code}` will be tested and eventually submitted. If the challenge relies on input, the
input will be passed to your function as `s`. All chalanges expect the results to be
printed to stdout. Your code will be tested against CPython 3.12 on a Linux machine.

Run `make test` to test your solutions and `make submit` to submit them. Have fun.



Challange "{code}":
{name}

{desc}


'''


def {code}a(s): print()
"""},
}


def bootstrap_challanges(path):
    path.mkdir(exist_ok=True)

    with open(path / '.dir-locals.el', 'w') as cf:
        cf.write('''((nil . ((indent-tabs-mode . nil)
          (python-indent-offset . 1)
          (eval . (autopep8-format-on-save-mode -1))))
 (js-mode . ((js-indent-level . 1))))''')
        cf.flush()

    for code, props in CHALLENGES.items():
        for lang in LANGS.values():
            chf = path / f"{code}.{lang['ext']}"
            if not chf.exists():
                with open(chf, 'w') as tf:
                    tf.write(lang['template'].format(code=code,
                                                     name=text2art(props['name']),
                                                     desc=props['desc']))
                    hprint(f'Created {tf.name}')


def get_implementations(path):
    ret = collections.defaultdict(dict)
    for lang, props in LANGS.items():
        for file_ in sorted(glob.glob(str(Path(path) / f'*.{props["ext"]}'))):
            src = Path(file_)
            ret[lang][src.stem] = props['discover'](src)

    return ret


def test_implementations(path):
    impls = get_implementations(path)

    for lang, props in LANGS.items():
        hprint(f'\n<b>Looking for {lang} challanges</b>')
        if not impls[lang]:
            print(' - No implementations found')
            continue

        for ch, funcs in impls[lang].items():
            if challenge := CHALLENGES.get(ch):
                if not funcs:
                    continue

                hprint(f' - <i>{ch}:</i> {challenge["name"]}')
                for func in funcs:
                    err = ''
                    try:
                        result = props['test'](func['body'], challenge)
                    except Exception as e:
                        trace = traceback.format_exc().replace('<', '').replace('>', '')
                        result, err = False, f'\n\n<ansired>{trace}</ansired>'
                    status = '<ansigreen>[P]</ansigreen>' if result else '<ansired>[F]</ansired>'
                    hprint(f"   - {status} <u>{func['name']}</u> {func['len']} chars{err}")


def submit_implementations(path, username, server=SERVER):
    for lang, chs in get_implementations(path).items():
        for ch, attempts in chs.items():
            challenge = CHALLENGES[ch]
            for attempt in attempts:
                try:
                    hprint(f"Submitting <b>{attempt['name']}</b> ({lang} challenge '{challenge['name']}')")
                    resp = requests.post(f'{server}/submit',
                                         data=dict(username=username,
                                               challenge=ch,
                                               src=attempt['body'],
                                               language=lang),
                                         timeout=10)
                    resp.raise_for_status()
                    verdict = resp.json()
                    status = '<ansigreen>[P]</ansigreen>' if verdict['tests'] else '<ansired>[F]</ansired>'
                    hprint(f"   - tests: {status}, {verdict['chars']} chars")
                except Exception as e:
                    hprint(f'   - <ansired>Failed to submit: {traceback.format_exc()}</ansired>')


def get_leaderboards(server=SERVER, limit=10):
    resp = requests.get(f'{server}/leaderboards?limit={limit}', timeout=10)
    resp.raise_for_status()

    return resp.json()
