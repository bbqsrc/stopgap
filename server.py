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
from tornado.options import options, define
from collections import OrderedDict

define("port", default=8888, type=int)
define("static", default="./static")

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
        self.elections = Connection().stopgap.elections
        self.ballots = Connection().stopgap.ballots


class BallotHandler(RequestHandler):
    def get_election(self, slug, id):
        election = self.application.elections.find_one({"slug": slug})
        if election is None:
            self.write("No ballot found.")
            return None, None

        now = datetime.datetime.utcnow()
        if election.get('startTime') is not None and election['startTime'] > now:
            self.write("This ballot has not begun yet, sorry!")
            return None, None
            #raise HTTPError(403, 'not started yet')
        if election.get('endTime') is not None and election['endTime'] < now:
            self.write("This ballot has now finished, sorry!")
            return None, None
            #raise HTTPError(403, 'has ended')

        token = uuid.UUID(id)
        if token not in election['tokens']:
            self.write("Invalid token.")
            return None, None
            #raise HTTPError(403, 'no token')

        if self.application.ballots.find_one({"election_id": election['_id'], "token": token}):
            self.write("You have already filled this ballot.")
            return None, None
            #raise HTTPError(409, "You have already filled this ballot.")

        return election, token

    def get_arguments_as_json(self):
        o = OrderedDict()
        for name, value in self.request.arguments.items():
            chunks = re.split(r'[\]\[\.]+', name.strip(']'))
            v = o
            for chunk in chunks[:-1]:
                if v.get(chunk) is None:
                    v[chunk] = OrderedDict()
                v = v[chunk]
            v[chunks[-1]] = value[0].decode()
        return o

    def get(self, slug, id):
        election, token = self.get_election(slug, id)
        if election is None:
            return
        self.write(election['html']['ballot'])

    def post(self, slug, id):
        election, token = self.get_election(slug, id)
        if election is None:
            return
        o = OrderedDict([
            ("election_id", election['_id']),
            ("token", token),
            ("ballot", self.get_arguments_as_json())
        ])
        res = safe_insert(self.application.ballots, o)
        if res is False:
            self.write(election['html']['failure'])
            return
        self.write(election['html']['success'])


class HomeHandler(StaticFileHandler):
    def get(self):
        super().get('index.html')

if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = Application([
        (r"/static/(.*)", StaticFileHandler, {"path": options.static}),
        (r"/(.*)/(.*)", BallotHandler),
        (r"/", HomeHandler, {"path": "."})
    ])
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
