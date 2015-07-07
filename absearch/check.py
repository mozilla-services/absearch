import sys
import os
import json
import argparse

from absearch.settings import SearchSettings


DEFAULT_DATADIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Simple HTTP Load runner.')
    parser.add_argument('-d', '--data-dir', help='Data directory',
                        type=str, default=DEFAULT_DATADIR)
    parser.add_argument('-c', '--config-file', help='Config File',
                        type=str, default='config.json')
    parser.add_argument('-s', '--schema-file', help='Schema File',
                        type=str, default='config.schema.json')

    args = parser.parse_args(args=args)

    print('Validating file...')
    configpath = os.path.join(args.data_dir, args.config_file)
    schemapath = os.path.join(args.data_dir, args.schema_file)

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
        return 1

    print('OK')
    return 0
