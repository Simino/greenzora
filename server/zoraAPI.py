from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.error import NoRecordsMatchError
from datetime import datetime
from server import db, utils
from server.models import ServerSetting, OperationParameter, create_or_update_paper

# The metadata prefix defines the format of the metadata
METADATA_PREFIX = 'oai_dc'


# Set up the API header
def create_connection():
    zora_url = ServerSetting.query.filter_by(name='zora_url').first().value
    registry = MetadataRegistry()
    registry.registerReader(METADATA_PREFIX, oai_dc_reader)
    client = Client(zora_url, registry)
    return client


# Gets one specific paper from the ZORA repository
def get_record(uid):
    client = create_connection()
    record = client.getRecord(identifier=uid, metadataPrefix=METADATA_PREFIX)
    metadata_dict = parse_record(record)
    create_or_update_paper(metadata_dict)


# Gets the papers from the ZORA repository and stores them in the database
def get_records():
    client = create_connection()
    args = {'metadataPrefix': METADATA_PREFIX}

    # If we previously pulled data from ZORA, only get the recent changes of the repository
    last_zora_pull = OperationParameter.query.filter_by(name='last_zora_pull').first()
    if last_zora_pull.value:
        args['from_'] = utils.parse_db_value(last_zora_pull.value, last_zora_pull.type_name)
    # We want to store the starting time to update last_zora_pull when we are done
    new_last_zora_pull = datetime.utcnow()

    # We get the papers in batches of 100 from zora, but can iterate through ALL entries because listRecords returns
    # an iterable pseudo-list (in the background there is still one API request per 100 papers).
    if utils.is_debug():
        count = 0
    try:
        for record in client.listRecords(**args):
            metadata_dict = parse_record(record)
            create_or_update_paper(metadata_dict)
            if utils.is_debug():
                count += 1
                print('\nCOUNT: ' + str(count) + '\n\n')
                #if count >= 100:
                #    break
        last_zora_pull.value = new_last_zora_pull
        db.session.commit()
    except NoRecordsMatchError as error:
        print(error)
        print('No records were found')


# We parse the received metadata from the record in the form of a dictionary where all fields but uid are lists
def parse_record(record):
    metadata_dict = {}
    if record[1]:
        metadata_dict = dict(record[1].getMap())
    metadata_dict['uid'] = record[0].identifier()

    # If the field subject contains a comma separated list, it is a list of keywords. Otherwise it is the subject.
    if 'subject' in metadata_dict:
        subject_list = []
        keyword_list = []
        for item in metadata_dict['subject']:
            if item.find(',') != -1:
                for keyword in item.split(','):
                    keyword_list.append(keyword)
            else:
                subject_list.append(item)
        metadata_dict['subject'] = subject_list
        metadata_dict['keyword'] = keyword_list

    return metadata_dict
