from server import server_app, db, login
from datetime import datetime
import dateutil.parser
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from flask_login import UserMixin


# TODO: Fix column types (string length!) + properties (nullable, etc.)


# ------------ DATABASE MODELS ---------------

# The Paper table stores all scientific papers with their metadata and their corresponding classification
# uid:                  The uid of the paper
# title:                The title of the paper
# creators:             The authors of the paper ([Paper] many to many [Creator])
# institutes:           The institutes of the paper ([Paper] many to many [Institute])
# ddcs:                 The dewey decimal classifications of the paper ([Paper] many to many [DDC])
# keywords:             The keywords of the paper ([Paper] many to many [Keyword])
# description:          The abstract of the paper
# publisher:            The publisher of the paper ([Paper] many to one [Publisher])
# date:                 The publishing date of the paper
# resource_types:       The resource types of the paper ([Paper] many to many [Type])
# language:             The language of the paper ([Paper] many to one [Language])
# relation:             The link to the ZORA page of the paper
# sustainable:          Flag that tells us whether a paper is sustainable or not
# annotated:            Flag that tells us whether a paper is annotated or not
class Paper(db.Model):
    __tablename__ = 'papers'
    uid = db.Column(db.String(256), primary_key=True)
    title = db.Column(db.String(256))
    creators = db.relationship('Creator', secondary='paper_creator_association_table')
    institutes = db.relationship('Institute', secondary='paper_institute_association_table')
    ddcs = db.relationship('DDC', secondary='paper_ddc_association_table')
    keywords = db.relationship('Keyword', secondary='paper_keyword_association_table')
    description = db.Column(db.Text())
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher')
    date = db.Column(db.DateTime)
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
            output += 'creator: ' + (str(creator.last_name) + ', ' + str(creator.first_name) if creator is not None else 'NULL') + '\n'
        for institute in self.institutes:
            output += 'institute: ' + (str(institute.name) if institute is not None else 'NULL') + '\n'
        for ddc in self.ddcs:
            output += 'dewey decimal classification: ' + (str(ddc.dewey_number) + ' ' + str(ddc.name) if ddc is not None else 'NULL') + '\n'
        for keyword in self.keywords:
            output += 'keyword: ' + (str(keyword.name) if keyword is not None else 'NULL') + '\n'
        output += 'description: ' + (self.description if self.description is not None else 'NULL') + '\n'
        output += 'publisher: ' + (str(self.publisher.name) if self.publisher is not None else 'NULL') + '\n'
        output += 'date: ' + (str(self.date) if self.date is not None else 'NULL') + '\n'
        for resource_type in self.resource_types:
            output += 'resource_type: ' + (str(resource_type.name) if resource_type is not None else 'NULL') + '\n'
        output += 'language: ' + (str(self.language.name) if self.language is not None else 'NULL') + '\n'
        output += 'relation: ' + (self.relation if self.relation is not None else 'NULL') + '\n'
        output += 'sustainable: ' + (str(self.sustainable) if self.sustainable is not None else 'NULL') + '\n'
        output += 'annotated: ' + (str(self.annotated) if self.annotated is not None else 'NULL') + '\n'
        return output

    # Creates or updates a Paper based on its metadata dictionary and returns it. It will also create the corresponding
    # Creators, Institutes, Dewey Decimal Classifications, Keywords, Publisher, ResourceTypes and Language if necessary.
    @classmethod
    def create_or_update(cls, metadata_dict):
        uid = metadata_dict['uid']
        title = metadata_dict['title'] if 'title' in metadata_dict else None
        creator_list = metadata_dict['creators'] if 'creators' in metadata_dict else []
        institute_list = metadata_dict['institutes'] if 'institutes' in metadata_dict else []
        ddc_list = metadata_dict['ddcs'] if 'ddcs' in metadata_dict else []
        keyword_list = metadata_dict['keywords'] if 'keywords' in metadata_dict else []
        description = metadata_dict['description'] if 'description' in metadata_dict else None
        publisher = metadata_dict['publisher'] if 'publisher' in metadata_dict else None
        date_string = metadata_dict['date'] if 'date' in metadata_dict else None

        # Zora has some fucked up dates (ex. 2009-11-31). If we encounter a invalid date, we set it to None.
        try:
            date = dateutil.parser.parse(date_string, default=datetime(1970, 1, 1))
        except ValueError as error:
            # TODO: Remove print statement --> debug only
            print(date_string + ': ' + str(error))
            date = None

        resource_type_list = metadata_dict['resource_types'] if 'resource_types' in metadata_dict else []
        language = metadata_dict['language'] if 'language' in metadata_dict else None
        relation = metadata_dict['relation'] if 'relation' in metadata_dict else None
        sustainable = metadata_dict['sustainable'] if 'sustainable' in metadata_dict else None
        annotated = metadata_dict['annotated'] if 'annotated' in metadata_dict else False

        # Create or merge the relational objects.

        # Create creators if they don't exist
        creators = []
        for creator_name in creator_list:
            split = creator_name.split(',')
            last_name = split[0]
            first_name = split[1] if len(split) >= 2 else None
            creator = Creator.get_or_create(first_name, last_name)
            creators.append(creator)

        # Create institutes if they don't exist
        institutes = []
        for institute_name in institute_list:
            institute = Institute.get_or_create(institute_name)
            institutes.append(institute)

        # Create ddcs if they don't exist
        ddcs = []
        for ddc_string in ddc_list:
            dewey_number, name = ddc_string.split(' ', 1)
            ddc = DDC.get_or_create(dewey_number, name)
            ddcs.append(ddc)

        # Create keywords if they don't exist
        keywords = []
        for keyword_name in keyword_list:
            keyword = Keyword.get_or_create(keyword_name)
            keywords.append(keyword)

        # Create resource_types if they don't exist
        resource_types = []
        for resource_type_name in resource_type_list:
            resource_type = ResourceType.get_or_create(resource_type_name)
            resource_types.append(resource_type)

        # Create publisher if it does not exist
        publisher_name = publisher
        if publisher_name:
            publisher = Publisher.get_or_create(publisher_name)

        # Create language if it does not exist
        language_name = language
        if language_name:
            language = Language.get_or_create(language_name)

        # Create or update paper
        paper = cls(uid=uid,
                    title=title,
                    creators=creators,
                    institutes=institutes,
                    ddcs=ddcs,
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

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    @classmethod
    def get_or_create(cls, first_name, last_name):
        creator = db.session.query(cls).filter(cls.first_name == first_name, cls.last_name == last_name).first()
        if not creator:
            creator = cls(first_name, last_name)
            db.session.add(creator)
        return creator

    @classmethod
    def get_top10_authors(cls):
        author_list = db.session.query(cls.first_name, cls.last_name, func.count(cls.id).label('count')).join(Paper, Creator.papers).filter(Paper.sustainable == True).group_by(cls.id).order_by('count DESC').limit(10).all()
        return author_list


class PaperCreator(db.Model):
    __tablename__ = 'paper_creator_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    creator_id = db.Column(db.Integer, db.ForeignKey('creators.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))
    creator = db.relationship(Creator, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))


class Institute(db.Model):
    __tablename__ = 'institutes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256))
    parent_id = db.Column(db.Integer, db.ForeignKey('institutes.id'))
    children = db.relationship('Institute', backref=db.backref('parent', remote_side=id))
    papers = db.relationship('Paper', secondary='paper_institute_association_table')

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_or_create(cls, name):
        institute = db.session.query(cls).filter(cls.name == name).first()
        if not institute:
            institute = cls(name)
            db.session.add(institute)
        return institute

    @classmethod
    def get_top10_institutes(cls):
        institute_list = db.session.query(cls.name, func.count(cls.id).label('count')).join(Paper, Institute.papers).filter(Paper.sustainable == True).group_by(cls.id).order_by('count DESC').limit(10).all()
        return institute_list


class PaperInstitute(db.Model):
    __tablename__ = 'paper_institute_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'))
    paper = db.relationship(Paper, backref=db.backref('paper_institute_association_table', cascade='all, delete-orphan'))
    institute = db.relationship(Institute, backref=db.backref('paper_institute_association_table', cascade='all, delete-orphan'))


# Dewey Decimal Classifications
class DDC(db.Model):
    __tablename__ = 'ddcs'
    dewey_number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    papers = db.relationship('Paper', secondary='paper_ddc_association_table')

    def __init__(self, dewey_number, name):
        self.dewey_number = dewey_number
        self.name = name

    @classmethod
    def get_or_create(cls, dewey_number, name):
        ddc = db.session.query(cls).get(dewey_number)
        if not ddc:
            ddc = cls(dewey_number, name)
            db.session.add(ddc)
        return ddc

    @classmethod
    def get_top10_ddcs(cls):
        ddc_list = db.session.query(cls.dewey_number, cls.name, func.count(cls.id).label('count')).join(Paper, DDC.papers).filter(Paper.sustainable == True).group_by(cls.id).order_by('count DESC').limit(10).all()
        return ddc_list


class PaperDDC(db.Model):
    __tablename__ = 'paper_ddc_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(256), db.ForeignKey('papers.uid'))
    ddc_dewey_number = db.Column(db.Integer, db.ForeignKey('ddcs.dewey_number'))
    paper = db.relationship(Paper, backref=db.backref('paper_ddc_association_table', cascade='all, delete-orphan'))
    ddc = db.relationship(DDC, backref=db.backref('paper_ddc_association_table', cascade='all, delete-orphan'))


class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)
    papers = db.relationship('Paper', secondary='paper_keyword_association_table')

    def __init__(self, name):
        self.name = name

    # TODO: We need to flush
    @classmethod
    def get_or_create(cls, name):
        keyword = db.session.query(cls).filter(cls.name == name).first()
        if not keyword:
            keyword = cls(name)
            db.session.add(keyword)
        return keyword

    @classmethod
    def get_top10_keywords(cls):
        keyword_list = db.session.query(cls.name, func.count(cls.id).label('count')).join(Paper, Keyword.papers).filter(Paper.sustainable == True).group_by(cls.id).order_by('count DESC').limit(10).all()
        return keyword_list


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

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_or_create(cls, name):
        publisher = db.session.query(cls).filter(cls.name == name).first()
        if not publisher:
            publisher = cls(name)
            db.session.add(publisher)
        return publisher


class ResourceType(db.Model):
    __tablename__ = 'resource_types'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    papers = db.relationship('Paper', secondary='paper_resource_type_association_table')

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_or_create(cls, name):
        resource_type = db.session.query(cls).filter(cls.name == name).first()
        if not resource_type:
            resource_type = cls(name)
            db.session.add(resource_type)
        return resource_type


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

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_or_create(cls, name):
        language = db.session.query(cls).filter(cls.name == name).first()
        if not language:
            language = cls(name)
            db.session.add(language)
        return language


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
        if not server_setting:
            return None
        value = server_setting.value
        parsed_value = server_setting.type.parse_value(value)
        return parsed_value

    # Sets the value of a specific ServerSetting
    @classmethod
    def set(cls, name, value):
        server_setting = db.session.query(cls).get(name)
        server_setting.value = value
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

    # Gets the value of a specific OperationParameter with the correct type if it exists. Otherwise it returns None.
    @classmethod
    def get(cls, name):
        operation_parameter = db.session.query(cls).get(name)
        if not operation_parameter:
            return None
        value = operation_parameter.value
        parsed_value = operation_parameter.type.parse_value(value)
        return parsed_value

    # Sets the value of a specific OperationParameter
    @classmethod
    def set(cls, name, value):
        operation_parameter = db.session.query(cls).get(name)
        operation_parameter.value = value
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

        # Parse the value based on its type and return it. All values are stored as strings in the database.
        if self.name == 'string':

            # Strings can be returned without processing
            return value
        elif self.name == 'int':

            # Integers need to get casted.
            return int(value)
        elif self.name == 'datetime':

            # Datetimes need to get parsed
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif self.name == 'boolean':

            # Booleans need to get casted.
            return bool(int(value))


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
    database_initialized = OperationParameter.get('database_initialized')
    if database_initialized:
        print('Database already initialized')
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
    OperationParameter.set('database_initialized', True)
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
    db.session.add(OperationParameter(name='legacy_annotations_imported', value=False, type=type_boolean))
    db.session.commit()

# ------------ END INITIALIZE DATABASE ---------------
