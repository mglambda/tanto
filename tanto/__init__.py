import os

_ROOT = os.path.abspath(os.path.dirname(__file__))
def get_tanto_data(path):
    return os.path.join(_ROOT, 'data', path)

def get_tanto_version():
    file = os.path.join(_ROOT, "__VERSION__")
    if os.path.isfile(file):
        return open(file, "r").read()
    return "unknown"


