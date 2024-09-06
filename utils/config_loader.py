import json


def load_test_data(config_file='config/test_data.json'):
    with open(config_file, 'r') as file:
        return json.load(file)
