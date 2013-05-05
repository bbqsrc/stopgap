import argparse
from shared import export_elections

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slugs', nargs='*')
    p.add_argument('-p', '--participants', action="store_true",
            help="Output participants (consider privacy concerns)")
    args = p.parse_args()
    print(export_elections(args.slugs, args.participants))
