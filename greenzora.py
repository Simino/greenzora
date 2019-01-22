from server import server_app

if __name__ == '__main__':
    server_app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
