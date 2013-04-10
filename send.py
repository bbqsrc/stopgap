import argparse
from shared import create_tokens_and_send_email

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slug')
    p.add_argument('--dry-run', '-d', action="store_true")
    args = p.parse_args()
    create_tokens_and_send_email(args.slug, args.dry_run)

