import io
import sys
from contextlib import contextmanager


import importlib.resources as pkg_resources

@contextmanager
def capture_output():
    standard_out = sys.stdout
    try:
        stdout = io.StringIO()
        sys.stdout = stdout
        yield stdout
    finally:
        sys.stdout = standard_out
        sys.stdout.flush()


def get_file(filename: str) -> io.StringIO: 
    return pkg_resources.read_text('tests.resources', filename)