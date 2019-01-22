from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from datetime import datetime
from server import db, models

# The ZORA repository URL. If it is changed, the server needs to be restarted.
URL = models.Setting.query.filter_by(name='zora_url').first()

# The metadata prefix defines the format of the metadata
METADATA_PREFIX = 'oai_dc'

# Set up the API handler
registry = MetadataRegistry()
registry.registerReader(METADATA_PREFIX, oai_dc_reader)
client = Client(URL, registry)


# Gets one specific paper from the ZORA repository
def get_record(uid):
    record = client.getRecord(identifier=uid, metadataPrefix=METADATA_PREFIX)
    print(record)
    return record


# Gets all papers from the ZORA repository
def get_records():
    record_list = []
    args = {'metadataPrefix': METADATA_PREFIX}

    # If we previously pulled data from ZORA, only get the recent changes of the repository
    last_zora_pull = models.OperationParameter.query.filter_by(name='last_zora_pull').first()
    if last_zora_pull.value:
        args['from_'] = last_zora_pull.value

    # Before we start the pull from ZORA, we update the last_zora_pull OperationParameter
    last_zora_pull.value = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    db.session.commit()

    # We get the papers in batches of 100 (listRecords returns a pseudo-list).
    # We store the papers in a real list to make it easier to use.
    for record in client.listRecords(**args):
        record_list.append(record)
    return record_list
