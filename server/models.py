from server import server_app, db

# TODO: Fix column types + properties (nullable, etc.)
# TODO: What is contributor (Paper metadata)?


# ------------ PAPER METADATA ---------------

# The Paper table stores all scientific papers with their metadata and their corresponding classification
# uid: The uid of the paper
# title: The title of the paper
# creators: The authors of the paper ([Paper] many to many [Creator])
# subjects: The subjects of the paper ([Paper] many to many [Subject])
# keywords: The keywords of the paper ([Paper] many to many [Keyword])
# description: The abstract of the paper
# publisher: The publisher of the paper ([Paper] many to one [Publisher])
# date: The publishing date of the paper
# resource_types: The resource types of the paper ([Paper] many to many [Type])
# language: The language of the paper ([Paper] many to one [Language])
# sustainable: Flag that tells us whether a paper is sustainable or not
class Paper(db.Model):
    __tablename__ = 'papers'
    uid = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200))
    creators = db.relationship('Creator', secondary='paper_creator_association_table')
    subjects = db.relationship('Subject', secondary='paper_subject_association_table')
    keywords = db.relationship('Keyword', secondary='paper_keyword_association_table')
    description = db.Column(db.Text())
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher')
    date = db.Column(db.String(30))
    resource_types = db.relationship('ResourceType', secondary='paper_resource_type_association_table')
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'))
    language = db.relationship('Language')
    sustainable = db.Column(db.Boolean, nullable=False)

    # TODO: Include all fields
    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return 'Paper: ' + self.uid + ' - sustainable: ' + self.sustainable


class Creator(db.Model):
    __tablename__ = 'creators'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(60))
    last_name = db.Column(db.String(60), nullable=False)
    papers = db.relationship('Paper', secondary='paper_creator_association_table')


class PaperCreator(db.Model):
    __tablename__ = 'paper_creator_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    creator_id = db.Column(db.Integer, db.ForeignKey('creators.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))
    creator = db.relationship(Creator, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    papers = db.relationship('Paper', secondary='paper_subject_association_table')


class PaperSubject(db.Model):
    __tablename__ = 'paper_subject_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))
    subject = db.relationship(Subject, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))


class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    papers = db.relationship('Paper', secondary='paper_keyword_association_table')


class PaperKeyword(db.Model):
    __tablename__ = 'paper_keyword_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))
    keyword = db.relationship(Keyword, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))


class Publisher(db.Model):
    __tablename__ = 'publishers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)


class ResourceType(db.Model):
    __tablename__ = 'resource_types'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    papers = db.relationship('Paper', secondary='paper_resource_type_association_table')


class PaperResourceType(db.Model):
    __tablename__ = 'paper_resource_type_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    resource_type_id = db.Column(db.Integer, db.ForeignKey('resource_types.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))
    resource_type = db.relationship(ResourceType, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))


class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)

# ------------ END PAPER METADATA ---------------


# ------------ SETTINGS & PARAMETERS ---------------

# Stores the different settings of the server
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)                     # The name of the setting
    value = db.Column(db.String(60), nullable=False)                    # The value of the setting

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value


# Stores server parameters such as the timestamp of the last pull from ZORA
class OperationParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)                     # The name of the parameter
    value = db.Column(db.String(60))                                    # The value of the parameter

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value


# TODO: Needed?
# The different types that settings and parameter tables can have.
# 1 = int
# 2 = string
# 3 = date
class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.id + ': ' + self.name

# ------------ END SETTINGS & PARAMETERS ---------------


# ------------ CLI COMMANDS ---------------

# Initialize the database
@server_app.cli.command()
def init_db():
    """Initializes the database"""
    db.create_all()
    print('Database created')
    initialize_db()
    print('Database initialized')


# Delete the database
@server_app.cli.command()
def delete_db():
    """Deletes the database and it's metadata"""
    db.drop_all()
    print('Database deleted')
    db.metadata.clear()
    print('Metadata cleared')


# Reset the database
@server_app.cli.command('reset_db')
def reset_db():
    """Resets the database"""
    delete_db()
    print('Database dropped')
    init_db()


# TODO: Initialize database properly (settings + operationParameters)
# Initialize the database
def initialize_db():
    initialize_default_settings()
    initialize_operation_parameters()


def initialize_default_settings():
    db.session.add(Setting(name='setting1', value='value1'))
    db.session.add(Setting(name='setting2', value='value2'))
    db.session.commit()


def initialize_operation_parameters():
    db.session.add(OperationParameter(name='lastZoraPull'))

# ------------ END CLI COMMANDS ---------------
