import argparse
from shared import end_election

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slug')
    args = p.parse_args()
    end_election(args.slug)

