import argparse
from shared import create_election

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('slug')
    p.add_argument('userlist', type=argparse.FileType('r'))
    p.add_argument('ballot_html', type=argparse.FileType('r'))
    p.add_argument('success_html', type=argparse.FileType('r'))
    p.add_argument('failure_html', type=argparse.FileType('r'))
    p.add_argument('email', type=argparse.FileType('r'))
    p.add_argument('email_author')
    p.add_argument('email_subject')

    args = p.parse_args()
    print(args)
    create_election(args.slug, args.userlist, args.ballot_html, args.success_html, args.failure_html, args.email, args.email_author, args.email_subject)


