# MongrEvent

MongrEvent is a proof-of-concept for writing a [Mongrel2](http://mongrel2.org/) message handler in Python and splitting the processing into a pipeline of [coroutines](http://en.wikipedia.org/wiki/Coroutine).

Mongrel2 is a web server by [Zed Shaw](http://zedshaw.com/). Mongrel2 handles everything having to do with HTTP and has facilities for passing request handling to external services using [ZeroMQ](http://www.zeromq.org/). MongrEvent is an example of how that service could be written to use [Eventlet](http://eventlet.net/) for coroutines. We also get [non-blocking I/O](http://en.wikipedia.org/wiki/Asynchronous_I/O) very [cheaply](http://eventlet.net/doc/patching.html).

The Mongrel2 handling code is based on Zed's python in mongrel2's source.

## Code

The code is on github: [https://github.com/j2labs/mongrevent](https://github.com/j2labs/mongrevent).

# The Design

Mongrel2 is configured to only answer on `/echo/`, or `http://localhost:6767/echo/`. Mongrel2 receives the reqeuest and forwards it down `tcp://127.0.0.1:9999`, where `handling.py` is listening. This socket is a Push socket from ZeroMQ.

*Read about the different socket types ZeroMQ offers in [the manual](http://api.zeromq.org/zmq_socket.html)*.

When `handling.py` is initialized, it sets up an input and output zmq socket for mongrel2. It's my personal preference to remember input and output instead of push and publish, the actual zeromq socket types used.

A coroutine is started to handle each request. The assumption is that a routing system could live in this coroutine. Once a route is determined, a subsequent coroutine is created to handle the request. A third coroutine is then created to handle the result of that request, like a postprocessing system.

The third coroutine responds to Mongrel2 by sending it's response on `handling.py`'s Pub socket. Mongrel2 picks up the message and then responds, completing the request.

# Mongrel2

If you're new to Mongrel2, you should read Zed's documentation on mongrel2.org. The rest of this doc assumes you've installed it successfully.

## Mongrel2 Config

The gist of it is that we have one host that answers to `/echo/`. Requests to `/echo/` go to our zmq handler.

    echo_handler = Handler(
        send_spec='tcp://127.0.0.1:9999',
        send_ident='34f9ceee-cd52-4b7f-b197-88bf2f0ec378',
        recv_spec='tcp://127.0.0.1:9998', 
        recv_ident='')
    
    j2_host = Host(
        name="localhost", 
        routes={'/echo/': echo_handler})
    
    j2_serv = Server(
        uuid="f400bf85-4538-4f7a-8908-67e313d515c2",
        access_log="/logs/access.log",
        error_log="/logs/error.log",
        chroot="./",
        default_host="localhost",
        name="j2 test",
        pid_file="/pids/mongrel2.pid",
        port=6767,
        hosts = [j2_host])
    
    settings = {"zeromq.threads": 1}
    
    servers = [j2_serv]

## Running it

Load the config and start mongrel2 up. It doesn't matter that we don't have a handler up yet.

    $ m2sh load --config env/j2.conf --db j2.db
    $ m2sh start -db j2.db -host localhost
    
You should see mongrel2 register a PUSH socket and a SUB socket as it's last lines of output.

# Python

I have stored the essential parts of my Python environment in a requirements file. I was not able to install pyzmq with pip and have it honor zeromq being installed in `/opt/local` so I install that separately.

    $ mkvirtualenv mongrevent
    (mongrevent) $ pip install -I -r ./requirements.txt
    
Now for pyzmq. This requires zeromq, so if please install if necessary.

    (mongrevent) $ cd ~/Desktop/
    (mongrevent) $ git clone git://github.com/zeromq/pyzmq.git
    (mongrevent) $ git checkout v2.0.10
    (mongrevent) $ # cp setup.cfg.template to setup.cfg and edit if necessary
    (mongrevent) $ python ./setup.py install

Assuming that worked, you should be able to turn on `handling.py`.

    (mongrevent) $ ./handling.py
    System online ]-----------------------------------

# Testing it

Just load up [http://localhost:6767/echo/](http://localhost:6767/echo/) with curl and see how it responds. You should see the same as below.

    $ curl "localhost:6767/echo/"
    /ohce/
