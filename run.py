from greenzora import server_app

# This will run the greenzora app. We do it this way for debug only, so that we can debug in pycharm.
if __name__ == '__main__':
    server_app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
