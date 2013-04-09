import pymongo
import uuid

def go():
    record = generate_record()
    record['email'] = email.read()
    record['html'] = html.read()
    record['error_html'] = error_html.read()
    record['success_html'] = success_html.read()
    insert_record(record)


def start():
    record['startDate'] = datetime.datetime.utcnow()
    send_emails(record)

# cli.py <userlist.csv> <email.txt> <ballot.html> <thanks.html> <error.html>
