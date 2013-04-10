import argparse
from shared import add_email

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slug')
    p.add_argument('email')
    args = p.parse_args()
    add_email(args.slug, args.email)

