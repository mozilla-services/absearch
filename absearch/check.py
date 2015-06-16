import sys
import os
import json

from absearch.settings import SearchSettings
from konfig import Config


datadir = os.path.join(os.path.dirname(__file__), '..', 'data')
conf = os.path.join(os.path.dirname(__file__), '..', 'config', 'absearch.ini')


def main():
    print('Validating file...')

    config = Config(conf)

    config_file = config['absearch']['config']
    schema_file = config['absearch']['schema']

    configpath = os.path.join(datadir, config_file)
    schemapath = os.path.join(datadir, schema_file)

    def read_config():
        with open(configpath) as f:
            return json.loads(f.read())

    def read_schema():
        with open(schemapath) as f:
            return json.loads(f.read())

    try:
        SearchSettings(read_config, read_schema)
    except ValueError as e:
        print('Not a valid JSON file')
        print(str(e))
        return False

    print('OK')
    return True


if __name__ == '__main__':
    sys.exit(main() and 0 or 1)
