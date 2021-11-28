import shutil
from pathlib import Path

import pytest

import iocheck

ROOT = Path(__file__).parent.parent
EXAMPLES = ROOT / 'examples'


@pytest.fixture(autouse=True, scope="session")
def _enable_logging():
    iocheck.load_logger("TRACE")


@pytest.fixture
def example() -> Path:
    return EXAMPLES / 'echocat'


def test_echocat_example_is_working(tmp_path: Path, example: Path):
    _build_example(example, tmp_path)

    # run tests
    res = iocheck.execute_cmd("python",
                              ["-m", "iocheck",
                               "-T", f"{example}/io_tests",
                               f"{example}/build/echocat"
                               ], ws=tmp_path, cwd=ROOT)
    assert res.exit == 0


def _build_example(example: Path, ws_path: Path):
    build = example / 'build'
    if build.exists():
        shutil.rmtree(build)
    res = iocheck.execute_cmd("cmake", ['-B', 'build', '-G', 'Unix Makefiles'], ws=ws_path, cwd=example)
    assert res.exit == 0
    res = iocheck.execute_cmd("cmake", ['--build', 'build'], ws=ws_path, cwd=example)
    assert res.exit == 0
