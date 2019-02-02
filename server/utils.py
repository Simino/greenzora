from server import server_app

def is_debug():
    return server_app.config['DEBUG']
