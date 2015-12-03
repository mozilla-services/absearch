import argparse



def main():
    parser = argparse.ArgumentParser(description='abcheck')

    parser.add_argument('-s', '--server', help='ABSearch server endpoint.',
                        type=str, default='http://localhost:8080')

    parser.add_argument('-r', '--redis', help='Redis server endpoint.',
                        type=str, default='http://localhost:7777')

    parser.add_argument('-l', '--locale', help='Local and territory.',
                        type=str, default='fr-FR')

    parser.add_argument('-h', '--hits', help='Number of hits to perform.',
                        type=int, default=100000)

    args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    main()


if __name__ == '__main__':
    main()
