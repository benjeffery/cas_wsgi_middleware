import os
import logging
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.contrib.sessions import FilesystemSessionStore

import config
from cas import CASMiddleware

#This function is called if:
# Not authenticated
# the ignore_redirect regex matches the (full) url pattern
def ignored_callback(environ, start_response):
    response = Response('{"Error":"NotAuthenticated"}')
#    response.status = '401 Unauthorized'
    response.status = '200 OK'
    response.headers['Content-Type'] = 'application/json'

    return response(environ, start_response)

class MyApp(object):

#Nothing to do
#    def __init__(self, config):

    def dispatch_request(self, request, environ):
        user = environ.get('REMOTE_USER', 'guest')
        data ='Hello ' + user + '!'
        if 'REMOTE_USER' in environ:
          data += '<a href="/logout">Logout</a>'
        if 'HTTP_CAS_MEMBEROF' in environ:
          data += environ['HTTP_CAS_MEMBEROF']
        return Response(data, headers = { ('Content-type', 'text/html')})

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request, environ)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(with_static=True):
    app = MyApp()
    
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })

        if config.CAS_SERVICE != '':
          fs_session_store = FilesystemSessionStore()
          app.wsgi_app = CASMiddleware(app.wsgi_app, cas_root_url = config.CAS_SERVICE, logout_url = config.CAS_LOGOUT_PAGE, logout_dest = config.CAS_LOGOUT_DESTINATION, protocol_version = config.CAS_VERSION, casfailed_url = config.CAS_FAILURE_PAGE, entry_page = '/', session_store = fs_session_store, ignore_redirect = '(.*)\?datatype=', ignored_callback = ignored_callback, gateway_redirect = '(.*)/static/gateway(.*)')
    return app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    run_simple(config.HOSTNAME, config.PORT, app, use_debugger=True, use_reloader=True)


