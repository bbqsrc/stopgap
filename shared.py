import pymongo
import uuid
import datetime
import sys

from collections import OrderedDict
from pymongo import Connection
from bson.json_util import dumps
from bbqutils.email import sendmail, create_email

def safe_modify(col, query, update, upsert=False):
    for attempt in range(5):
        try:
            result = col.find_and_modify(
                    query=query,
                    update=update,
                    upsert=upsert,
                    new=True
            )
            return result
        except pymongo.errors.OperationFailure:
            return False
        except pymongo.errors.AutoReconnect:
            wait_t = 0.5 * pow(2, attempt)
            time.sleep(wait_t)
    return False


def safe_insert(collection, data):
    for attempt in range(5):
        try:
            collection.insert(data, safe=True)
            return True
        except pymongo.errors.OperationFailure:
            return False
        except pymongo.errors.AutoReconnect:
            wait_t = 0.5 * pow(2, attempt)
            time.sleep(wait_t)
    return False


def create_election(slug, userlist, ballot_html, success_html, failure_html, email, email_author, email_subject):
    elections = Connection().stopgap.elections

    election = elections.find_one({"slug": slug})
    if election is not None:
        raise Exception("There is already an election by the name of '%s'" % slug)

    election = {
        "slug": slug,
        "html": {
            "ballot": ballot_html.read(),
            "success": success_html.read(),
            "failure": failure_html.read()
        },
        "email": {
            "content": email.read(),
            "from": email_author,
            "subject": email_subject
        },
        "participants": [],
        "tokens": [],
        "startTime": datetime.datetime.utcnow()
    }

    # Convert into set to remove duplicates
    election['participants'] = [{"email": x.strip(), "sent": False} for x in set(userlist)]
    return safe_insert(elections, election)


def export_ballots(slugs):
    elections = Connection().stopgap.elections
    ballots = Connection().stopgap.ballots

    out = OrderedDict()
    for slug in slugs:
        election = elections.find_one({"slug": slug})
        if election is None:
            raise Exception("No election with slug.")

        o = list(ballots.find({"election_id": election['_id']}))
        out[slug] = o
    return dumps(out, indent=2)


def export_elections(slugs, keep_participants=False):
    elections = Connection().stopgap.elections

    out = OrderedDict()
    for slug in slugs:
        election = elections.find_one({"slug": slug})
        if election is None:
            raise Exception("No election with slug.")

        if not keep_participants:
            # protect email addresses of participants
            del election['participants']

        out[slug] = election
    return dumps(out, indent=2)


def add_email(slug, email):
    safe_modify(Connection().stopgap.elections, {"slug": slug}, {
        "$push": {"participants": {"email": email, "sent": False}}
    })


def end_election(slug):
    safe_modify(Connection().stopgap.elections, {"slug": slug}, {
        "$set": {"endTime": datetime.datetime.utcnow()}
    })


def update_html(slug, ballot_html):
    safe_modify(Connection().stopgap.elections, {"slug": slug}, {
        "$set": {"html.ballot": ballot_html.read()}
    })


def create_tokens_and_send_email(slug, dry_run=False, force=False):
    elections = Connection().stopgap.elections

    election = elections.find_one({"slug": slug})
    if election is None:
        raise Exception("There is no election by the name of '%s'" % slug)

    unsent = []
    for o in election['participants']:
        if o['sent'] is not True:
            unsent.append(o['email'])

    total_unsent = len(unsent)
    if not force:
        res = input("Are you sure you want to send %s emails?\n[y/N]>" % total_unsent)
        if res.lower() != "y":
            return

    for n, email in enumerate(unsent):
        sys.stdout.write("[%s/%s] %s... " % (n+1, total_unsent, email))
        token = uuid.uuid4()

        if not dry_run:
            res = safe_modify(elections, {"slug": slug}, {"$push": {"tokens": token}})
            if res is False:
                raise Exception("A token failed to be saved to the server: '%s'" % token.hex)

        mail = create_email(
                frm=election['email']['from'],
                subject=election['email']['subject'],
                to=email,
                text=election['email']['content'].format(
                    slug=slug,
                    token=token.hex
                )
        )

        if not dry_run:
            sendmail(mail)
            res = safe_modify(elections, {"slug": slug, "participants.email": email},
                {"$set": {"participants.$.sent": True}})
            if res is False:
                raise Exception("An email sent flag failed to be set for '%s'" % email)
        print("Sent!")

# cli.py <election-slug> <userlist.csv> <email.txt> <ballot.html> <thanks.html> <error.html>
