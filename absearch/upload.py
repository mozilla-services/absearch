import os
from konfig import Config

from absearch.check import main as check
from absearch.aws import set_s3_file

datadir = os.path.join(os.path.dirname(__file__), '..', 'data')
conf = os.path.join(os.path.dirname(__file__), '..', 'config', 'absearch.ini')


def main():
    check()
    config = Config(conf)
    config_file = config['absearch']['config']
    schema_file = config['absearch']['schema']

    for file_ in (config_file, schema_file):
        filename = os.path.join(datadir, file_)
        print('Uploading %r' % filename)
        set_s3_file(filename, config)

    print('Done')


if __name__ == '__main__':
    main()
