import pymongo
import tornado.options
import tornado.web
import re
import uuid
import datetime
import logging

from bson.json_util import dumps
from pymongo import Connection
from tornado.web import HTTPError, RequestHandler, StaticFileHandler


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


class Application(tornado.web.Application):
    def __init__(self, handlers, **settings):
        tornado.web.Application.__init__(self, handlers, **settings)
        self.ballots = Connection().stopgap.ballots


class BallotHandler(RequestHandler):
    def get_ballot(self, slug, id):
        ballot = self.application.ballots.find_one({"slug": slug})
        if ballot is None:
            raise HTTPError(404)

        #TODO do time checks for start and finish

        id = uuid.UUID(id)
        token = self.application.ballots.find_one({
            "slug": slug,
            "tokens._id": id
        }, fields=["tokens.$"])
        if token is None:
            raise HTTPError(403)
        token = token['tokens'][0]

        if token.get('ballot') is not None:
            raise HTTPError(409, "You have already filled this ballot.")

        return ballot, token

    def get_arguments_as_json(self):
        o = {}
        print(self.request.arguments)
        for name, value in self.request.arguments.items():
            chunks = re.split(r'[\]\[]+', name.strip(']'))
            print(chunks)
            v = o
            for chunk in chunks[:-1]:
                if v.get(chunk) is None:
                    v[chunk] = {}
                v = v[chunk]
            v[chunks[-1]] = value[0].decode()
        print(o)
        return o

    def get(self, slug, id):
        ballot, token = self.get_ballot(slug, id)
        self.write(ballot['html'])

    def post(self, slug, id):
        ballot, token = self.get_ballot(slug, id)
        logging.debug(token)
        safe_modify(self.application.ballots, {
                "slug": slug,
                "tokens._id": token["_id"]
            }, {
                "$set": {
                    "tokens.$.ballot": self.get_arguments_as_json()
                }
            }
        )


def create_test_ballot():
    ballots = Connection().stopgap.ballots
    ballots.remove({"slug": "test"})
    o = {
        "slug": "test",
        "html": """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <form method="post">
                <input name="test"><br>
                <input name="elections[test]"><br>
                <input type="submit">
            </form>
        </body>
        </html>""",
        "participants": [{
            "_id": uuid.uuid4(),
            "email": "test@test.me"
        }],
        "tokens": [{
            "_id": uuid.UUID("0" * 32)
        },{
            "_id": uuid.UUID("1" * 32)
        }],
        "startTime": datetime.datetime.utcnow()
    }
    ballots.insert(o)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = Application([
        (r"/(.*)/(.*)", BallotHandler)
    ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
