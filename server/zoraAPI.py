from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.error import NoRecordsMatchError
from datetime import datetime


class ZoraAPI:

    def __init__(self, url, metadata_prefix):
        registry = MetadataRegistry()
        registry.registerReader(metadata_prefix, oai_dc_reader)
        self.client = Client(url, registry)

        self.metadata_prefix = metadata_prefix

    # Get all metadata dictionaries from
    def get_metadata_dicts(self, from_):
        record_list = self.get_records(from_)
        metadata_dict_list = self.parse_records(record_list)
        return metadata_dict_list

    # Gets one specific paper from the ZORA repository and returns the metadata from it
    def get_record(self, uid):
        record = self.client.getRecord(identifier=uid, metadataPrefix=self.metadata_prefix)

        return record

    # Gets the papers from the ZORA repository and returns their metadata in form of a list of dictionaries
    def get_records(self, from_):
        args = {'metadataPrefix': self.metadata_prefix}

        # Add the from_ argument if it is defined (this is used to get only the most recent papers/changes)
        if from_:
            args['from_'] = from_

        # Get the relevant papers from ZORA and parse them
        record_list = []
        try:
            record_list = self.client.listRecords(**args)
        except NoRecordsMatchError as error:
            print(error)
            print('No records were found')
        finally:
            return record_list

    # This function parses a record into a dictionary. It also splits up the 'subject' field into 'subjects' and 'keywords'.
    def parse_record(self, record):
        if not record[0] or not record[1]:
            return

        metadata_dict = dict(record[1].getMap())

        metadata_dict['uid'] = record[0].identifier()
        metadata_dict['creators'] = metadata_dict.pop('creator')

        # If the field 'subject' contains a comma separated list, it is a list of keywords. Otherwise it is a subject.
        subject_list = []
        keyword_list = []
        if 'subject' in metadata_dict:
            for item in metadata_dict['subject']:
                if item.find(',') != -1:
                    for keyword in item.split(','):
                        keyword_list.append(keyword)
                else:
                    subject_list.append(item)
        metadata_dict['subjects'] = subject_list
        metadata_dict['keywords'] = keyword_list
        metadata_dict['resource_types'] = metadata_dict.pop('type')

        return metadata_dict

    # This function parses the a record from ZORA in a easier to use dictionary.
    def parse_records(self, record_list):
        metadata_dict_list = []
        count = 0
        for record in record_list:
            metadata_dict = self.parse_record(record)
            if metadata_dict:
                metadata_dict_list.append(metadata_dict)
            count += 1
            if count >= 5000:
                break;
        return metadata_dict_list
