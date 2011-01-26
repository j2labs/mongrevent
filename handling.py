#!/usr/bin/env python
#
# 

"""This is a rough sketch of what it looks like to put Mongrel2, pyzmq
and eventlet together.

I am interested in criticisms of the design. jdennis at gmail.
"""

import eventlet
from eventlet import spawn, spawn_n, serve
from eventlet.green import zmq
from eventlet.hubs import get_hub, use_hub
use_hub('zeromq')

from uuid import uuid1
import os
import sys

from mongrel2 import Mongrel2Connection, http_response
from functools import partial


ctx = zmq.Context()
pool = eventlet.GreenPool()


###
### Request handling 
###

def route_request(m2c, request):
    """This coroutine is probably an application level call. It would inspect
    the request and figure out which request handler to load, if multiple were
    in use for a single zmq handler.

    For now it just launches the follow up handler.
    """
    print '  > request routing coroutine called'
    spawn_n(request_handler, m2c, request)
        
def request_handler(m2c, request):
    """Coroutine for handling the request itself. It simply returns the request
    path in reverse for now.
    """
    print '  > request handler coroutine called'
    rev_msg = ''.join(reversed(request.path))
    response = http_response(rev_msg, 200, 'OK', {})
    spawn_n(result_handler, m2c, request, response)

    return (request, response)

def result_handler(m2c, request, response):
    """The request has been processed and this is called to do any post
    processing and then send the data back to mongrel2.
    """
    print '  > shipping response: %s' % (response)
    m2c.reply(request, response)


###
### Application logic
###
        
if __name__ == '__main__':
    usage = 'usage: handling <pull address> <pub address>'
    if len (sys.argv) != 3:
        print usage
        sys.exit(1)

    sender_id = '82209006-86FF-4982-B5EA-D1E29E55D481'
    pull_addr = sys.argv[1]
    pub_addr = sys.argv[2]
    pool = eventlet.GreenPool()

    m2c = Mongrel2Connection(sender_id, pull_addr, pub_addr)

    print 'System online ]-----------------------------------'
    while True:
        try:
            request = m2c.recv()
            pool.spawn_n(route_request, m2c, request)
        except Exception, e:
            print 'System is going offline\n  Reason: %s' % e
            break
