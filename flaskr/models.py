from flaskr import db

class Classification(db.Model):
    uid = db.Column(db.String(120), primary_key=True)       # The uid of the paper from ZORA
    sustainable = db.Column(db.Boolean(), nullable=False)   # Flag that tells us whether a paper is sustainable or not

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return 'Paper: ' + self.uid + ' - sustainable: ' + self.sustainable

# TODO
#class Settings(db.Model):
#    classInterval = db.Column TODO: Rather key-value pairs?