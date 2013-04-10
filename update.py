import argparse
from shared import update_html

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slug')
    p.add_argument('ballot_html', type=argparse.FileType('r'))
    args = p.parse_args()
    update_html(args.slug, args.ballot_html)

