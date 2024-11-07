import ast
import importlib
import inspect
import json
import logging
import shlex
import subprocess
import tempfile
from pathlib import Path

from prompt_toolkit import HTML, print_formatted_text

log = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent


def hprint(html):
    print_formatted_text(HTML(html))


def run_shell_cmd(cmd, input=None, cwd=None, env=None):
    log.debug('Running cmd %s', cmd)

    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    si = None
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        startupinfo=si)
    stdout, stderr = process.communicate(input)

    if process.poll():
        raise Exception(stderr)

    return True, cmd, stdout, stderr


def get_user():
    return run_shell_cmd('whoami')[2].strip()


def get_js_functions(path, prefix='ch'):
    ok, cmd, stdout, stderr = run_shell_cmd(f'node {HERE / "jsrip.js"} {path} {prefix}')
    if ok:
        return json.loads(stdout)
    else:
        return []


def get_py_functions(path, prefix='ch'):
    funcs = []

    try:
        module = importlib.import_module(f'{path.parent.stem}.{path.stem}')
        with open(module.__file__, encoding='utf8') as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith(prefix):
                    func = inspect.getsource(getattr(module, node.name))
                    body = func.split(':', 1)[1]
                    funcs.append({'name': node.name, 'body': body, 'len': len(body)})
    except Exception as e:
        log.error('Failed to parse module "%s": %s\nAre you sure, there is no syntax error?', path, e)

    return funcs


def test_py(src, challenge):
    for inp, out in challenge['tests']:
        with tempfile.NamedTemporaryFile(suffix='.py') as tf:
            path = Path(tf.name)
            tf.write(f's="{inp}"\ndef test(s):\n{src}\n\ntest(s)'.encode())
            tf.flush()
            ok, cmd, stdout, stderr = run_shell_cmd(f'python3 -m {path.stem}',
                                                  env={'PYTHONPATH': path.parent})
            if stdout[:-1] != out:  # strip nl
                return False

    return True


def test_js(src, challenge):
    for inp, out in challenge['tests']:
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(f'''s="{inp}";
{src}'''.encode())
            tf.flush()
            ok, cmd, stdout, stderr = run_shell_cmd(f'node {HERE / "eval.js"} {tf.name}')
            if stdout.removesuffix('\n') != out:
                return False

        return True
