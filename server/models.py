from server import server_app, db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# TODO: Fix column types (string length!) + properties (nullable, etc.)


# ------------ DATABASE MODELS ---------------

# The Paper table stores all scientific papers with their metadata and their corresponding classification
# uid:              The uid of the paper
# title:            The title of the paper
# creators:         The authors of the paper ([Paper] many to many [Creator])
# subjects:         The subjects of the paper ([Paper] many to many [Subject])
# keywords:         The keywords of the paper ([Paper] many to many [Keyword])
# description:      The abstract of the paper
# publisher:        The publisher of the paper ([Paper] many to one [Publisher])
# date:             The publishing date of the paper
# resource_types:   The resource types of the paper ([Paper] many to many [Type])
# language:         The language of the paper ([Paper] many to one [Language])
# relation:         The link to the ZORA page of the paper
# sustainable:      Flag that tells us whether a paper is sustainable or not
# annotated:        Flag that tells us whether a paper is annotated or not
class Paper(db.Model):
    __tablename__ = 'papers'
    uid = db.Column(db.String(256), primary_key=True)
    title = db.Column(db.String(256))
    creators = db.relationship('Creator', secondary='paper_creator_association_table')
    subjects = db.relationship('Subject', secondary='paper_subject_association_table')
    keywords = db.relationship('Keyword', secondary='paper_keyword_association_table')
    description = db.Column(db.Text())
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher')
    date = db.Column(db.String(64))
    resource_types = db.relationship('ResourceType', secondary='paper_resource_type_association_table')
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'))
    language = db.relationship('Language')
    relation = db.Column(db.String(256))
    sustainable = db.Column(db.Boolean)
    annotated = db.Column(db.Boolean, default=False)

    # TODO: Check if this is easier to do somehow
    # Method that defines how an object of this class is printed. Useful for debugging.
    # If no value is set, print 'NULL'
    def __repr__(self):
        output = 'uid: ' + self.uid + '\n'
        output += 'title: ' + (self.title if self.title is not None else 'NULL') + '\n'
        for creator in self.creators:
            output += 'creator: ' + (str(creator.last_name) + str(creator.first_name) if creator is not None else 'NULL') + '\n'
        for subject in self.subjects:
            output += 'subject: ' + (str(subject.name) if subject is not None else 'NULL') + '\n'
        for keyword in self.keywords:
            output += 'keyword: ' + (str(keyword.name) if keyword is not None else 'NULL') + '\n'
        output += 'description: ' + (self.description if self.description is not None else 'NULL') + '\n'
        output += 'publisher: ' + (str(self.publisher.name) if self.publisher is not None else 'NULL') + '\n'
        output += 'date: ' + (self.date if self.date is not None else 'NULL') + '\n'
        for resource_type in self.resource_types:
            output += 'resource_type: ' + (str(resource_type.name) if resource_type is not None else 'NULL') + '\n'
        output += 'language: ' + (str(self.language.name) if self.language is not None else 'NULL') + '\n'
        output += 'relation: ' + (self.relation if self.relation is not None else 'NULL') + '\n'
        output += 'sustainable: ' + (str(self.sustainable) if self.sustainable is not None else 'NULL') + '\n'
        output += 'annotated: ' + (str(self.annotated) if self.annotated is not None else 'NULL') + '\n'
        return output

    # Creates or updates a Paper based on its metadata dictionary and returns it. It will also create the corresponding
    # Creators, Subjects, Keywords, Publisher, ResourceTypes and Language if necessary.
    @classmethod
    def create_or_update(cls, metadata_dict):
        uid = metadata_dict['uid']
        title = metadata_dict['title'][0] if 'title' in metadata_dict and metadata_dict['title'] else None
        creator_list = metadata_dict['creators'] if 'creators' in metadata_dict else []
        subject_list = metadata_dict['subjects'] if 'subjects' in metadata_dict else []
        keyword_list = metadata_dict['keywords'] if 'keywords' in metadata_dict else []
        description = metadata_dict['description'][0] if 'description' in metadata_dict and metadata_dict[
            'description'] else None
        publisher = metadata_dict['publisher'][0] if 'publisher' in metadata_dict and metadata_dict[
            'publisher'] else None
        date = metadata_dict['date'][0] if 'date' in metadata_dict and metadata_dict['date'] else None
        resource_type_list = metadata_dict['resource_types'] if 'resource_types' in metadata_dict else []
        language = metadata_dict['language'][0] if 'language' in metadata_dict and metadata_dict[
            'language'] else None
        relation = metadata_dict['relation'][0] if 'relation' in metadata_dict and metadata_dict[
            'relation'] else None

        # Only exist in legacy annotations
        sustainable = metadata_dict['sustainable'] if 'sustainable' in metadata_dict else None
        annotated = metadata_dict['annotated'] if 'annotated' in metadata_dict else False

        # Create creators if they don't exist
        creators = []
        for creator_name in creator_list:
            split = creator_name.split(',')
            last_name = split[0]
            first_name = split[1] if len(split) >= 2 else None
            creator = Creator(first_name=first_name, last_name=last_name)
            creators.append(db.session.merge(creator))

        # Create subjects if they don't exist
        subjects = []
        for subject_name in subject_list:
            subject = Subject(name=subject_name)
            subjects.append(db.session.merge(subject))

        # Create keywords if they don't exist
        keywords = []
        for keyword_name in keyword_list:
            keyword = Keyword(name=keyword_name)
            keywords.append(db.session.merge(keyword))

        # Create resource_types if they don't exist
        resource_types = []
        for resource_type_name in resource_type_list:
            resource_type = ResourceType(name=resource_type_name)
            resource_types.append(db.session.merge(resource_type))

        # Create publisher if it does not exist
        publisher_name = publisher
        if publisher_name:
            publisher = Publisher(name=publisher_name)
            db.session.merge(publisher)

        # Create language if it does not exist
        language_name = language
        if language_name:
            language = Language(name=language_name)
            db.session.merge(language)

        # Create or update paper
        paper = cls(uid=uid,
                    title=title,
                    creators=creators,
                    subjects=subjects,
                    keywords=keywords,
                    description=description,
                    publisher=publisher,
                    date=date,
                    resource_types=resource_types,
                    language=language,
                    relation=relation,
                    sustainable=sustainable,
                    annotated=annotated)

        # If there already exists a paper with the same uid, it will be merged (updated) and otherwise created.
        paper = db.session.merge(paper)
        db.session.commit()

        return paper

    def set_annotation(self, sustainable):
        self.sustainable = sustainable
        self.annotated = True


class Creator(db.Model):
    __tablename__ = 'creators'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    papers = db.relationship('Paper', secondary='paper_creator_association_table')


class PaperCreator(db.Model):
    __tablename__ = 'paper_creator_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    creator_id = db.Column(db.Integer, db.ForeignKey('creators.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))
    creator = db.relationship(Creator, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256))
    papers = db.relationship('Paper', secondary='paper_subject_association_table')


class PaperSubject(db.Model):
    __tablename__ = 'paper_subject_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))
    subject = db.relationship(Subject, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))


class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    papers = db.relationship('Paper', secondary='paper_keyword_association_table')


class PaperKeyword(db.Model):
    __tablename__ = 'paper_keyword_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))
    keyword = db.relationship(Keyword, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))


class Publisher(db.Model):
    __tablename__ = 'publishers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256))


class ResourceType(db.Model):
    __tablename__ = 'resource_types'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    papers = db.relationship('Paper', secondary='paper_resource_type_association_table')


class PaperResourceType(db.Model):
    __tablename__ = 'paper_resource_type_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    resource_type_id = db.Column(db.Integer, db.ForeignKey('resource_types.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))
    resource_type = db.relationship(ResourceType, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))


class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))


# Stores the different settings of the server.
# zora_url:             The base URL for requests to the zora API (string)
# zora_pull_interval:   The amount of days between different ZORA repository pulls (int)
class ServerSetting(db.Model):
    __tablename__ = 'settings'
    name = db.Column(db.String(64), primary_key=True)                     # The name of the setting
    value = db.Column(db.String(64), nullable=False)                    # The value of the setting
    type_name = db.Column(db.String(64), db.ForeignKey('types.name'))    # The type of the value
    type = db.relationship('Type')

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value

    # Gets the value of a specific ServerSetting with the correct type
    @classmethod
    def get(cls, name):
        server_setting = db.session.query(cls).get(name)
        value = server_setting.value
        parsed_value = server_setting.type.parse_value(value)
        return parsed_value

    # Sets the value of a specific ServerSetting
    @classmethod
    def set(cls, name, value):
        server_setting = db.session.query(cls).get(name)
        server_setting.value = value
        db.session.commit()
        return server_setting


# Stores server parameters.
# last_zora_pull:       Timestamp of the date, when the server did the last pull from ZORA (datetime)
# zora_pull_interval:   The time in days between different pull requests from the ZORA repository (int)
class OperationParameter(db.Model):
    __tablename__ = 'operation_parameters'
    name = db.Column(db.String(64), primary_key=True)                     # The name of the parameter
    value = db.Column(db.String(64))                                    # The value of the parameter
    type_name = db.Column(db.String(64), db.ForeignKey('types.name'))    # The type of the value
    type = db.relationship('Type')

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value

    # Gets the value of a specific OperationParameter with the correct type
    @classmethod
    def get(cls, name):
        operation_parameter = db.session.query(cls).get(name)
        value = operation_parameter.value
        parsed_value = operation_parameter.type.parse_value(value)
        return parsed_value

    # Sets the value of a specific OperationParameter
    @classmethod
    def set(cls, name, value):
        operation_parameter = db.session.query(cls).get(name)
        operation_parameter.value = value
        db.session.commit()
        return operation_parameter


# The different types that settings and parameter tables can have.
# int:          An integer value
# datetime:     A datetime value
# boolean:      A boolean value
class Type(db.Model):
    __tablename__ = 'types'
    name = db.Column(db.String(64), primary_key=True)

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name

    # Parses the value (String) of a ServerSetting or OperationParameter to the corresponding type
    def parse_value(self, value):

        # If there is no value, we don't have to parse anything
        if value is None:
            return None

        # Parse the value based on its type and return it
        if self.name == 'string':
            return value
        elif self.name == 'int':
            return int(value)
        elif self.name == 'datetime':
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif self.name == 'boolean':
            return True if value == 'True' else False


class Translation(db.Model):
    __tablename__ = 'translations'
    name = db.Column(db.String(256), primary_key=True)
    eng = db.Column(db.String(1024))
    de = db.Column(db.String(1024))


class User(UserMixin, db.Model):
    __tablename = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.String(128))

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------ END DATABASE MODELS ---------------


# ------------ INITIALIZE DATABASE ---------------

def initialize_db():

    # Create the database tables if they don't already exist
    db.create_all()

    # Set the default values if the database was not already initialized
    database_initialized = db.session.query(OperationParameter).get('database_initialized')
    if database_initialized:
        return

        # Initialize the default types
    initialize_types()
    print('Types initialized')

    # Initialize the default settings
    initialize_default_settings()
    print('Default settings initialized')

    # Initialize the default operation parameters
    initialize_operation_parameters()
    print('Operation parameters initialized')

    # Remember that the database was initialized
    database_initialized = db.session.query(OperationParameter).get('database_initialized')
    database_initialized.value = True
    db.session.commit()

    print('Database initialized')


def initialize_types():
    db.session.add(Type(name='int'))
    db.session.add(Type(name='datetime'))
    db.session.add(Type(name='string'))
    db.session.add(Type(name='boolean'))
    db.session.commit()


def initialize_default_settings():
    type_string = db.session.query(Type).get('string')
    type_int = db.session.query(Type).get('int')
    db.session.add(ServerSetting(name='zora_url', value=server_app.config['DEFAULT_ZORA_URL'], type=type_string))
    db.session.add(ServerSetting(name='zora_pull_interval', value=server_app.config['DEFAULT_ZORA_PULL_INTERVAL'], type=type_int))
    db.session.commit()


def initialize_operation_parameters():
    type_datetime = db.session.query(Type).get('datetime')
    type_boolean = db.session.query(Type).get('boolean')
    db.session.add(OperationParameter(name='last_zora_pull', type=type_datetime))
    db.session.add(OperationParameter(name='database_initialized', value=False, type=type_boolean))
    db.session.commit()

# ------------ END INITIALIZE DATABASE ---------------
