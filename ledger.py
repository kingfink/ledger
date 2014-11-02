import os.path
import time
import redis

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options
define('port', default=8000, help='run on the given port', type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class WritePageHandler(tornado.web.RequestHandler):
    def post(self):
        # get the input data
        person = self.get_argument('person')
        group = self.get_argument('group')
        description = self.get_argument('description')
        amount = self.get_argument('amount')

        # save the data to Redis
        r_server = redis.Redis(host="localhost")

        # person - belong to 1 to many groups
        person_id = 'person:' + person.lower().replace(' ', '-')
        person_name = person

        # add the person if they do not exist
        if not r_server.exists(person_id):
            r_server.hmset(person_id, {'name': person_name})

        # group - have 1 to many people, have 1 to many purchases
        group_id = 'group:' + group.lower().replace(' ', '-')
        group_members_id = 'group-members:' + group.lower().replace(' ', '-')
        group_name = group
        group_person = person_id

        # add the group (& group-members) if the group doesn't exist
        if not r_server.exists(group_id):
            r_server.sadd(group_members_id, group_person)
            r_server.hmset(group_id, {'name': group_name,
                                      'members': group_members_id})

        # attempt to add the person to the group
        r_server.sadd(group_members_id, person_id)

        # purchase - belongS to 1 people & 1 groups
        purchase_id = 'purchase:' + person.lower().replace(' ', '-') + '-' + str(r_server.time()[0]) \
                      + '-' + str(r_server.time()[1])
        purchase_ts = r_server.time()
        description = description
        amount = float(amount)
        purchase_person = person_id
        purchase_group = group_id

        # add the purchase
        r_server.hmset(purchase_id, {'ts': purchase_ts,
                                     'description': description,
                                     'amount': float(amount),
                                     'person': purchase_person,
                                     'group': purchase_group})

        # render the page
        self.render('write.html', person=person, group=group, description=description, amount=amount,
                    date=time.strftime("%d/%m/%Y"))

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r'/', IndexHandler), (r'/write', WritePageHandler)],
                                  template_path=os.path.join(os.path.dirname(__file__), 'templates'))
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()