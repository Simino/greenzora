from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader

URL = 'https://www.zora.uzh.ch/cgi/oai2'
METADATA_PREFIX = 'oai_dc'

registry = MetadataRegistry()
registry.registerReader(METADATA_PREFIX, oai_dc_reader)
client = Client(URL, registry)

count = 0

# Gets one specific paper from the ZORA repository
def get_record(uid):
    record = client.getRecord(identifier=uid, metadataPrefix=METADATA_PREFIX)
    return record

# Gets all papers from the ZORA repository.
def get_records():
    record_list = []
    for record in client.listRecords(metadataPrefix=METADATA_PREFIX):
        record_list.append(record)
    return record_list



