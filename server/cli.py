from server import server_app, db

# ------------ CLI COMMANDS ---------------

# Delete the database
@server_app.cli.command('delete_db')
def delete_db():
    """Deletes the database and it's metadata"""
    db.drop_all()
    print('Database deleted')
    db.metadata.clear()
    print('Metadata cleared')

# ------------ END CLI COMMANDS ---------------
