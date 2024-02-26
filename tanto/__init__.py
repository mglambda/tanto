import os

_ROOT = os.path.abspath(os.path.dirname(__file__))
def get_tanto_data(path):
    return os.path.join(_ROOT, 'data', path)




