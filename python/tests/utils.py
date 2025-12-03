import os

def get_test_data_path(path):
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "test_data", path)
