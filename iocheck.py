#! /usr/bin/env python3
import argparse
import datetime
import enum
import filecmp
import inspect
import logging
import logging.config
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Type

PYTHON_REQUIRED = "3.8"
VERSION = '0.0.1-alpha'
__version__ = VERSION
NAME = "iocheck"
DESC = """
"""

# Logging specific stuff
LOG = logging.getLogger(NAME)

TRACE = 5
logging.addLevelName(TRACE, 'TRACE')


def log_trace(self, msg, *args, **kwargs):
    self.log(TRACE, msg, *args, **kwargs)


logging.Logger.trace = log_trace

###
# Tests discovery
###

ALLOWED_SUFFIXES = ('.in', '.out', '.err', '.exit', '.arg')


class TestDf:
    def __init__(self, root_dir: Path, test_dir: Path, name: str):
        self.test_subdir: Path = test_dir
        self.root_dir: Path = root_dir
        self.name = name

    @property
    def rel_path(self) -> Path:
        return self.test_subdir.relative_to(self.root_dir)

    def namespace(self, sep='_') -> str:
        return sep.join(p for p in self.test_subdir.parts)

    def full_name(self, sep='_') -> str:
        nm = self.namespace(sep) + sep if self.namespace() else ''
        return nm + self.name

    def exit(self) -> int:
        file = self._resolve_file('exit')
        if not file:
            return 0
        content = file.read_text()
        return int(content)

    def stdout(self) -> Optional[Path]:
        return self._resolve_file('out')

    def stderr(self) -> Optional[Path]:
        return self._resolve_file('err')

    def stdin(self) -> Optional[Path]:
        return self._resolve_file('in')

    def args(self) -> List[str]:
        file = self._resolve_file('arg')
        return list(file.read_text().splitlines()) if file else []

    def _resolve_file(self, ext: str) -> Optional['Path']:
        fp = self.root_dir / self.test_subdir / f'{self.name}.{ext}'
        return fp if fp.exists() else None


def gather_tests(root_dir: Path, test_dir: Path = Path('.')) -> List['TestDf']:
    test_names = set()
    tests = []
    full_dir = root_dir / test_dir
    for item in full_dir.glob("*"):
        if item.is_dir():
            res = gather_tests(root_dir, test_dir / item.name)
            tests.extend(res)
        if item.suffix not in ALLOWED_SUFFIXES:
            continue
        t_name = item.stem
        test_names.add(t_name)
    for tn in test_names:
        tests.append(TestDf(root_dir, test_dir, tn))
    return tests


class DynamicClassBase(unittest.TestCase):
    longMessage = True


def make_test_function(cfg: 'AppConfig', df: 'TestDf'):
    def test(self):
        ws = cfg.ws_path / df.test_subdir
        if not ws.exists():
            ws.mkdir(parents=True)
        res = execute_cmd(
            cfg.executable,
            args=df.args(),
            stdin=df.stdin(),
            ws=cfg.ws_path
        )
        self.assertEqual(res.exit, df.exit(), "Status code check failed")

        if df.stdout():
            self.assertTrue(filecmp.cmp(df.stdout(), res.stdout), _make_msg('STDOUT', df.stdout(), res.stdout))

        if df.stderr():
            self.assertTrue(filecmp.cmp(df.stderr(), res.stderr), _make_msg('STDERR', df.stderr(), res.stderr))

    return test


def _make_msg(name: str, expected, provided) -> str:
    return f"""{name} check failed
            Expected: {expected}
            Provided: {provided}
            DIFF: diff -u {expected} {provided}
            """


def create_suite(cfg: 'AppConfig', tests: List['TestDf']) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for i, test in enumerate(tests):
        test_func = make_test_function(cfg, test)
        clsname = f"IOCheckTest_{i}"
        test_name = f'{test.full_name("_")}'
        cls = type(
            clsname,
            (DynamicClassBase,),
            {
                test_name: test_func,
            }
        )
        suite.addTest(cls(test_name))

    return suite


###
# Executable execution
###


class CommandResult:
    def __init__(self, exit_code: int, stdout: Path, stderr: Path, elapsed: int):
        self.exit: int = exit_code
        self.stdout: Path = stdout
        self.stderr: Path = stderr
        self.elapsed: int = elapsed

    def __str__(self) -> str:
        return str({
            'exit': self.exit,
            'stdout': str(self.stdout),
            'stderr': str(self.stderr),
            'elapsed': self.elapsed,
        })

    def __repr__(self) -> str:
        return str(self)


def execute_cmd(cmd: str, args: List[str], ws: Path, stdin: Path = None,
                stdout: Path = None, stderr: Path = None, nm: str = None,
                log: logging.Logger = None, timeout: int = 60, cmd_prefix: List[str] = None,
                env: Dict[str, Any] = None, cwd: Union[str, Path] = None,
                **kwargs) -> 'CommandResult':
    # pylint: disable=R0914,R0913
    log = log or LOG
    log.info("[CMD] Exec: '%s' with args %s", cmd, str(args))
    log.debug(" -> [CMD] Exec STDIN: '%s'", stdin if stdin else "EMPTY")
    log.trace(" -> [CMD] Exec with timeout %d, cwd: '%s'", timeout, cwd)
    if not nm:
        nm = cmd.split('/')[-1] + "_" + datetime.datetime.now().isoformat("_").replace(':', '-')
    stdout = stdout or ws / f'{nm}.stdout'
    stderr = stderr or ws / f'{nm}.stderr'

    full_env = {**os.environ, **(env or {})}

    with stdout.open('w') as fd_out, stderr.open('w') as fd_err:
        fd_in = Path(stdin).open('r') if stdin else None
        start_time = time.perf_counter_ns()
        try:
            cmd_prefix = cmd_prefix if cmd_prefix else []
            exec_result = subprocess.run(
                [*cmd_prefix, cmd, *args],
                stdout=fd_out,
                stderr=fd_err,
                stdin=fd_in,
                timeout=timeout,
                env=full_env,
                check=False,
                cwd=str(cwd) if cwd else None,
                **kwargs
            )
        except Exception as ex:
            log.error("[CMD] Execution '%s' failed: %s", cmd, ex)
            raise ex
        finally:
            end_time = time.perf_counter_ns()
            if fd_in:
                fd_in.close()

    log.debug("[CMD] Result[exit=%d]: %s", exec_result.returncode, str(exec_result))
    log.trace(" -> Command stdout '%s'", stdout)
    log.trace("STDOUT: %s", stdout.read_bytes())
    log.trace(" -> Command stderr '%s'", stderr)
    log.trace("STDERR: %s", stderr.read_text())

    return CommandResult(
        exit_code=exec_result.returncode,
        elapsed=end_time - start_time,
        stdout=stdout,
        stderr=stderr,
    )


###
# Logging
###

def load_logger(level: str = None, log_file: Optional[Path] = None, file_level: str = None):
    level = level if level else os.getenv("LOG_LEVEL", "warning")
    level = level.upper()
    file_level = file_level.upper() if file_level else level
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
            },
            'single': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'TRACE',
                'class': 'logging.StreamHandler',
                'formatter': 'single'
            },
        },
        'loggers': {
            NAME: {
                'handlers': ['console'],
                'level': level,
            }
        }
    }
    if log_file and log_file.parent.exists():
        log_config['handlers']['file'] = {
            'level': file_level,
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': str(log_file)
        }
        log_config['loggers'][NAME]['handlers'].append('file')
    logging.config.dictConfig(log_config)


###
# CLI AND MAIN
###


class AppConfig:
    def __init__(self, tests_path: Union[str, Path], ws_path: Union[str, Path], executable: str):
        self.tests_path: Path = Path(tests_path)
        self.ws_path: Path = Path(ws_path)
        self.executable: str = executable


def main(args):
    parser = make_cli_parser()
    args = parser.parse_args(args)
    load_logger()

    app_config = _make_config(args)
    tests = gather_tests(app_config.tests_path)
    if not tests:
        raise FileNotFoundError("No tests has been found")
    print(f"Found {len(tests)} tests:")
    for tn in tests:
        print(" *", tn.full_name('/'))
    print("\n *** RUNNING TESTS ***\n")

    suite = create_suite(app_config, tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def _resolve_tests_location(tests) -> Path:
    if tests:
        tests = Path(tests)
        if not tests.exists():
            raise FileNotFoundError(f"Provided test directory does not exists: {tests}")
        return tests
    # Lets try other locations:
    for loc in ('./iotests', './io_tests', './tests'):
        pth = Path(loc)
        if pth.exists():
            return pth
    raise FileNotFoundError(f"No tests can be found in the current directory: {Path.cwd()}")


def _make_config(args):
    tests = _resolve_tests_location(args.tests)
    ws_path = args.workspace
    if not ws_path:
        ws_path = tempfile.mktemp(prefix=f"{NAME}-")
    app_config = AppConfig(
        tests_path=tests,
        ws_path=ws_path,
        executable=args.executable
    )
    LOG.debug("Config: %s", app_config.__dict__)
    return app_config


def make_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(NAME, description=DESC)
    parser.set_defaults(func=None)
    parser.add_argument('--version', action='version', version=f'{NAME}: {VERSION}')
    parser.add_argument('executable', type=str,
                        help="Location of the executable you would like to df")
    parser.add_argument('-T', '--tests', type=str, help='Location of the tests directory',
                        default=None)
    parser.add_argument('-W', '--workspace', type=str,
                        help='Location of the testing workspace - outputs/artifacts',
                        default=None)
    return parser


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as e:
        print("Execution failed")
        print(e)
        exit(1)
