from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.error import NoRecordsMatchError
from server import db
from server.models import Institute, ResourceType
from http.client import RemoteDisconnected
import re


#
class ZoraAPI:
    METADATA_PREFIX = 'oai_dc'

    def __init__(self, url):
        registry = MetadataRegistry()
        registry.registerReader(ZoraAPI.METADATA_PREFIX, oai_dc_reader)
        self.client = Client(url, registry)
        self.institutes = {}
        self.resource_types = []
        self.load_institutes_and_types()

    def get_institutes(self):
        return self.institutes

    def get_resource_types(self):
        return self.resource_types

    def load_institutes_and_types(self):
        institutes_list = []
        resource_type_list = []
        for item in self.client.listSets():
            split = item[1].split(' = ')
            if len(split) != 2:
                continue
            set_type, set_value = split
            if set_type == 'Subjects':
                institutes_list.append(set_value)
            elif set_type == 'Type':
                resource_type_list.append(set_value)
        institutes_dict = self.parse_institutes(institutes_list)
        self.institutes = institutes_dict
        self.resource_types = resource_type_list

    @staticmethod
    def parse_institutes(institute_list_raw):
        institutes_dict = {}
        for institute_raw in institute_list_raw:
            institutes = institute_raw.split(': ')
            parent = institutes_dict
            for institute in institutes:
                if parent.get(institute) is None:
                    parent[institute] = {}
                parent = parent[institute]
        return institutes_dict

    # Get all metadata dictionaries from
    def get_metadata_dicts(self, from_):
        record_list = self.get_records(from_)
        metadata_dict_list = self.parse_records(record_list)
        return metadata_dict_list

    # Gets one specific paper from the ZORA repository and returns the metadata from it
    def get_record(self, uid):
        record = self.client.getRecord(identifier=uid, metadataPrefix=ZoraAPI.METADATA_PREFIX)

        return record

    # Gets the papers from the ZORA repository and returns their metadata in form of a list of dictionaries
    def get_records(self, from_):
        args = {'metadataPrefix': ZoraAPI.METADATA_PREFIX}

        # Add the from_ argument if it is defined (this is used to get only the most recent papers/changes)
        if from_:
            args['from_'] = from_

        # Get the relevant papers from ZORA and parse them
        record_list = []
        try:
            print('Loading records from ZORA API...')
            record_iterator = self.client.listRecords(**args)
            record_list = []
            count = 0
            for record in record_iterator:
                record_list.append(record)
                count += 1
                if count % 1000 == 0:
                    print(str(count))
                if count >= 2000:
                    break
            print(count)
            print('Done')
        except NoRecordsMatchError:
            print('No records were found')
        except RemoteDisconnected as error:
            # TODO: How to behave if disconnected? repeat? if yes, how many times and in what intervals?
            # TODO: Test if this works as intended
            print(error)
        except Exception as error:
            print(error)
        finally:
            return record_list

    # This method parses the a record from ZORA in a easier to use dictionary.
    def parse_records(self, record_list):
        metadata_dict_list = []
        print('Parsing records...')
        for record in record_list:
            metadata_dict = self.parse_record(record)
            if metadata_dict:
                metadata_dict_list.append(metadata_dict)
        print('Done')
        return metadata_dict_list

    # This function parses a record into a dictionary with a similar structure of the Paper database object.
    # To do so, it turns some unnecessary lists into single values and parses the 'subject' field into 'ddcs' (dewey
    # decimal classifications), 'keywords' and 'institutes'.
    #
    # NOTE: It is not possible to parse the 'subject' field properly since we lack the ability to distinguish between
    # keywords and institutes (some institutes contain commas --> they will get recognized as lists of keywords).
    @staticmethod
    def parse_record(record):
        metadata_dict = {}
        metadata_dict['uid'] = record[0].identifier()

        # If there is no metadata, we assume that the paper has been deleted and store that information in the dict
        if not record[1]:
            metadata_dict['deleted'] = True
            return metadata_dict

        # If there is metadata available, we parse it into a convenient form
        metadata_dict = {**metadata_dict, **dict(record[1].getMap())}

        metadata_dict['title'] = metadata_dict['title'][0] if 'title' in metadata_dict and len(metadata_dict['title']) > 0 else None
        metadata_dict['creators'] = metadata_dict.pop('creator') if 'creator' in metadata_dict else []

        # If the field 'subject' starts with three digits, it is a ddc (dewey decimal classification). If it contains a
        # comma-separated list, it is a list of keywords. Otherwise it is an institute.
        #
        # NOTE: There are some dewey decimal classifications that contain commas, therefore we check for the three
        # digits before we look for comma separated lists. Some institutes contain commas as well. This
        # leads to some institutes getting recognized as a list of keywords. With the information available this problem
        # unfortunately cannot be solved properly.
        institute_list = []
        ddc_list = []
        keyword_list = []
        if 'subject' in metadata_dict:
            for item in metadata_dict['subject']:

                # If subject starts with three digits and a space, we assume its a dewey decimal classification
                regex = re.compile('^\d\d\d\s+\w')
                if regex.match(item):
                    ddc_list.append(item)

                # If the subject has the same name as an institute, we assume it is an institute
                elif db.session.query(Institute).filter(Institute.name == item).first():
                    institute_list.append(item)

                # If it is none of the above, we assume that it is a comma-separated list of keywords
                else:
                    for keyword in item.split(','):
                        keyword_list.append(keyword)

        metadata_dict['institutes'] = institute_list
        metadata_dict['ddcs'] = ddc_list
        metadata_dict['keywords'] = keyword_list
        metadata_dict['description'] = metadata_dict['description'][0] if 'description' in metadata_dict and len(metadata_dict['description']) > 0 else None
        metadata_dict['publisher'] = metadata_dict['publisher'][0] if 'publisher' in metadata_dict and len(metadata_dict['publisher']) > 0 else None
        metadata_dict['date'] = metadata_dict['date'][0] if 'date' in metadata_dict and len(metadata_dict['date']) > 0 else None

        # We filter the 'type' field and only store the paper type
        type_list = metadata_dict.pop('type') if 'type' in metadata_dict else []
        resource_type_list = []
        for resource_type in type_list:
            if db.session.query(ResourceType).filter(ResourceType.name == resource_type).first():
                resource_type_list.append(resource_type)
        metadata_dict['resource_types'] = resource_type_list
        metadata_dict['language'] = metadata_dict['language'][0] if 'language' in metadata_dict and len(metadata_dict['language']) > 0 else None
        metadata_dict['relation'] = metadata_dict['relation'][0] if 'relation' in metadata_dict and len(metadata_dict['relation']) > 0 else None

        return metadata_dict
