import argparse
from shared import export_ballots

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slugs', nargs='*')
    args = p.parse_args()
    print(export_ballots(args.slug))
