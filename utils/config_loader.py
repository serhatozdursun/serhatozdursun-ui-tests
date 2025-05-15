import json
import os


def load_test_data(config_file: str = 'config/test_data.json') -> dict:
    """Load test data from a JSON file with absolute path resolution."""
    base_path = os.path.dirname(os.path.dirname(__file__))  # go up from utils/
    file_path = os.path.join(base_path, config_file)
    with open(file_path, 'r') as file:
        return json.load(file)