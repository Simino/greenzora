from server import server_app, db, scheduler, utils
from flask_sqlalchemy import event

# TODO: Fix column types (string length!) + properties (nullable, etc.)
# TODO: What is contributor (Paper metadata)?


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
class Paper(db.Model):
    __tablename__ = 'papers'
    uid = db.Column(db.String(200), primary_key=True)
    title = db.Column(db.String(200))
    creators = db.relationship('Creator', secondary='paper_creator_association_table')
    subjects = db.relationship('Subject', secondary='paper_subject_association_table')
    keywords = db.relationship('Keyword', secondary='paper_keyword_association_table')
    description = db.Column(db.Text())
    publisher_name = db.Column(db.String(200), db.ForeignKey('publishers.name'))
    publisher = db.relationship('Publisher')
    date = db.Column(db.String(30))
    resource_types = db.relationship('ResourceType', secondary='paper_resource_type_association_table')
    language_name = db.Column(db.String(200), db.ForeignKey('languages.name'))
    language = db.relationship('Language')
    relation = db.Column(db.String(200))
    sustainable = db.Column(db.Boolean)

    # Method that defines how an object of this class is printed. Useful for debugging.
    # If no value is set, print 'NULL'
    def __repr__(self):
        output = 'uid: ' + self.uid + '\n'
        output += 'title: ' + (self.title if self.title is not None else 'NULL') + '\n'
        for creator in self.creators:
            output += 'creator: ' + (creator.name if self.description is not None else 'NULL') + '\n'
        for subject in self.subjects:
            output += 'subject: ' + (subject.name if self.description is not None else 'NULL') + '\n'
        for keyword in self.keywords:
            output += 'keyword: ' + (keyword.name if self.description is not None else 'NULL') + '\n'
        output += 'description: ' + (self.description if self.description is not None else 'NULL') + '\n'
        output += 'publisher: ' + (self.publisher.name if self.publisher is not None else 'NULL') + '\n'
        output += 'date: ' + (self.date if self.date is not None else 'NULL') + '\n'
        for resource_type in self.resource_types:
            output += 'resource_type: ' + (resource_type.name if self.description is not None else 'NULL') + '\n'
        output += 'language: ' + (self.language.name if self.language is not None else 'NULL') + '\n'
        output += 'relation: ' + (self.relation if self.relation is not None else 'NULL') + '\n'
        output += 'sustainable: ' + (self.sustainable if self.sustainable is not None else 'NULL')
        return output


class Creator(db.Model):
    __tablename__ = 'creators'
    name = db.Column(db.String(60), primary_key=True)
    papers = db.relationship('Paper', secondary='paper_creator_association_table')


class PaperCreator(db.Model):
    __tablename__ = 'paper_creator_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    creator_name = db.Column(db.String(200), db.ForeignKey('creators.name'))
    paper = db.relationship(Paper, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))
    creator = db.relationship(Creator, backref=db.backref('paper_creator_association_table', cascade='all, delete-orphan'))


class Subject(db.Model):
    __tablename__ = 'subjects'
    name = db.Column(db.String(200), primary_key=True)
    papers = db.relationship('Paper', secondary='paper_subject_association_table')


class PaperSubject(db.Model):
    __tablename__ = 'paper_subject_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    subject_name = db.Column(db.String(200), db.ForeignKey('subjects.name'))
    paper = db.relationship(Paper, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))
    subject = db.relationship(Subject, backref=db.backref('paper_subject_association_table', cascade='all, delete-orphan'))


class Keyword(db.Model):
    __tablename__ = 'keywords'
    name = db.Column(db.String(60), primary_key=True)
    papers = db.relationship('Paper', secondary='paper_keyword_association_table')


class PaperKeyword(db.Model):
    __tablename__ = 'paper_keyword_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    keyword_name = db.Column(db.String(200), db.ForeignKey('keywords.name'))
    paper = db.relationship(Paper, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))
    keyword = db.relationship(Keyword, backref=db.backref('paper_keyword_association_table', cascade='all, delete-orphan'))


class Publisher(db.Model):
    __tablename__ = 'publishers'
    name = db.Column(db.String(200), primary_key=True)


class ResourceType(db.Model):
    __tablename__ = 'resource_types'
    name = db.Column(db.String(60), primary_key=True)
    papers = db.relationship('Paper', secondary='paper_resource_type_association_table')


class PaperResourceType(db.Model):
    __tablename__ = 'paper_resource_type_association_table'
    id = db.Column(db.Integer, primary_key=True)
    paper_uid = db.Column(db.String(200), db.ForeignKey('papers.uid'))
    resource_type_name = db.Column(db.String(200), db.ForeignKey('resource_types.name'))
    paper = db.relationship(Paper, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))
    resource_type = db.relationship(ResourceType, backref=db.backref('paper_resource_type_association_table', cascade='all, delete-orphan'))


class Language(db.Model):
    __tablename__ = 'languages'
    name = db.Column(db.String(60), primary_key=True)


# Stores the different settings of the server.
# zora_url:             The base URL for requests to the zora API (string)
# zora_pull_interval:   The amount of days between different ZORA repository pulls (int)
class ServerSetting(db.Model):
    __tablename__ = 'settings'
    name = db.Column(db.String(60), primary_key=True)                     # The name of the setting
    value = db.Column(db.String(60), nullable=False)                    # The value of the setting
    type_name = db.Column(db.String(60), db.ForeignKey('types.name'))    # The type of the value
    type = db.relationship('Type')

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value


# Stores server parameters.
# last_zora_pull:       Timestamp of the date, when the server did the last pull from ZORA (datetime)
# zora_pull_interval:   The time in days between different pull requests from the ZORA repository (int)
class OperationParameter(db.Model):
    __tablename__ = 'operation_parameters'
    name = db.Column(db.String(60), primary_key=True)                     # The name of the parameter
    value = db.Column(db.String(60))                                    # The value of the parameter
    type_name = db.Column(db.String(60), db.ForeignKey('types.name'))    # The type of the value
    type = db.relationship('Type')

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name + ': ' + self.value


# The different types that settings and parameter tables can have.
# int:          An integer value
# datetime:     A datetime value
class Type(db.Model):
    __tablename__ = 'types'
    name = db.Column(db.String(60), primary_key=True)

    # Method that defines how an object of this class is printed. Useful for debugging.
    def __repr__(self):
        return self.name

# ------------ END DATABASE MODELS ---------------


# ------------ INITIALIZE DATABASE ---------------

def initialize_db():
    db.create_all()

    # Initialize the default settings if the table is empty
    if Type.query.first() is None:
        initialize_types()
        print('Types initialized')

    # Initialize the default settings if the table is empty
    if ServerSetting.query.first()is None:
        initialize_default_settings()
        print('Default settings initialized')

    # Initialize the default operation parameters if the table is empty
    if OperationParameter.query.first() is None:
        initialize_operation_parameters()
        print('Operation parameters initialized')

    print('Database initialized')


def initialize_types():
    db.session.add(Type(name='int'))
    db.session.add(Type(name='datetime'))
    db.session.add(Type(name='string'))
    db.session.commit()


def initialize_default_settings():
    type_string = Type.query.filter_by(name='string').first()
    type_int = Type.query.filter_by(name='int').first()
    db.session.add(ServerSetting(name='zora_url', value='https://www.zora.uzh.ch/cgi/oai2', type=type_string))
    db.session.add(ServerSetting(name='zora_pull_interval', value='14', type=type_int))
    db.session.commit()


def initialize_operation_parameters():
    type_datetime = Type.query.filter_by(name='datetime').first()
    db.session.add(OperationParameter(name='last_zora_pull', type=type_datetime))
    db.session.commit()

# ------------ END INITIALIZE DATABASE ---------------


# ------------ CRUD FUNCTIONS ---------------

# Creates or updates a Paper based on its metadata dictionary. It will also create the corresponding Creators,
# Subjects, Keywords, Publisher, ResourceTypes, Language if necessary.
def create_or_update_paper(metadata_dict):
    uid = metadata_dict['uid']
    title = metadata_dict['title'][0] if 'title' in metadata_dict and metadata_dict['title'] else None
    creator_list = metadata_dict['creator'] if 'creator' in metadata_dict else []
    subject_list = metadata_dict['subject'] if 'subject' in metadata_dict else []
    keyword_list = metadata_dict['keyword'] if 'keyword' in metadata_dict else []
    description = metadata_dict['description'][0] if 'description' in metadata_dict and metadata_dict[
        'description'] else None
    publisher = metadata_dict['publisher'][0] if 'publisher' in metadata_dict and metadata_dict[
        'publisher'] else None
    date = metadata_dict['date'][0] if 'date' in metadata_dict and metadata_dict['date'] else None
    resource_type_list = metadata_dict['type'] if 'type' in metadata_dict else []
    language = metadata_dict['language'][0] if 'language' in metadata_dict and metadata_dict[
        'language'] else None
    relation = metadata_dict['relation'][0] if 'relation' in metadata_dict and metadata_dict[
        'relation'] else None

    # Create creators if they don't exist
    creators = []
    for creator_name in creator_list:
        creator = Creator(name=creator_name)
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
    paper = Paper(uid=uid,
                  title=title,
                  creators=creators,
                  subjects=subjects,
                  keywords=keywords,
                  description=description,
                  publisher=publisher,
                  date=date,
                  resource_types=resource_types,
                  language=language,
                  relation=relation)
    paper = db.session.merge(paper)
    db.session.commit()
    if utils.is_debug():
        print(paper)

# ------------ CRUD FUNCTIONS ---------------


# ------------ EVENT LISTENERS ---------------

# Handle setting changes
@event.listens_for(ServerSetting.value, 'set')
def handle_setting_change(target, value, oldvalue, initiator):
    setting_name = target.name

    if setting_name == 'zora_pull_interval':
        job = scheduler.get_job(id=server_app.config['ZORA_API_JOB_ID'])
        if job:
            job.reschedule(trigger='interval', minutes=value)

    print('Setting "' + setting_name + '" was changed to ' + str(value) + '.')

# ------------ END EVENT LISTENERS ---------------
