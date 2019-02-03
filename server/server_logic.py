from server.utils import is_debug
from server.models import Paper, ServerSetting, OperationParameter
from server.zoraAPI import ZoraAPI
from server.ml_tool import MLTool
from flask_sqlalchemy import event
from flask_apscheduler import APScheduler
from datetime import datetime
import pandas as pd
import json


class ServerLogic:
    ZORA_API_JOB_ID = 'zoraAPI_get_records_job'

    # Init stuff in __init__?
    def __init__(self, server_app, db):
        self.server_app = server_app
        self.db = db

        # Initialize the ZORA API
        url = ServerSetting.get('zora_url')
        self.zoraAPI = ZoraAPI(url)

        print('ZORA API initialized')

        # Import the annotations that are not stored in the database
        file_path = self.server_app.config['LEGACY_ANNOTATIONS_PATH']
        self.import_legacy_annotations(file_path)

        # Initialize the machine learning tool
        self.ml_tool = MLTool()

        # Get the relevant papers needed for the training
        training_data_set = pd.read_sql_query(self.db.session.query(Paper).filter(Paper.annotated == True).statement,
                                              self.db.session.bind)

        # Prepare the data that is needed for the training and train the classifier
        training_data_set['data'] = training_data_set["title"] + " | " + training_data_set["description"]
        training_data = training_data_set.data
        labels = training_data_set.sustainable
        self.ml_tool.train_classifier(training_data, labels)

        # Initialize the task scheduler
        self.scheduler = APScheduler()
        self.scheduler.init_app(server_app)
        self.scheduler.start()

        print('Task scheduler initialized')

        # Initialize the zora pull job, that pulls data from the ZORA repository in a fixed interval
        job_interval = ServerSetting.get('zora_pull_interval')
        server_app.apscheduler.add_job(func=self.zora_pull,
                                       trigger='interval',
                                       days=job_interval,
                                       next_run_time=datetime.now(),
                                       id=ServerLogic.ZORA_API_JOB_ID)

        print('ZORA pull job started')

        # Register the database event listener for the server settings table
        @event.listens_for(ServerSetting.value, 'set')
        def handle_setting_change(target, value, oldvalue, initiator):
            self.handle_setting_change(target, value, oldvalue, initiator)

        print('Database event handler registered')

        print('Server initialized')

    # This function gets the latest papers from ZORA, which are then classified and stored in the database.
    def zora_pull(self):

        # We want to store the starting time to update last_zora_pull when we are done
        new_last_zora_pull = datetime.utcnow()

        # Get the papers that were created or updated since the last pull
        from_ = OperationParameter.get('last_zora_pull')
        metadata_dict_list = self.zoraAPI.get_metadata_dicts(from_)

        # Store the papers in the database and classify the paper
        # TODO: metadata_dict empty!
        for index, metadata_dict in enumerate(metadata_dict_list):
            title = metadata_dict['title'][0] if ('title' in metadata_dict and len(metadata_dict['title']) != 0) else ''
            description = metadata_dict['description'][0] if ('description' in metadata_dict and len(metadata_dict['description']) != 0) else ''
            data = pd.Series([title + ' | ' + description])
            metadata_dict['sustainable'] = self.ml_tool.classify(data).item(0)

            Paper.create_or_update(metadata_dict)

            # if is_debug():
                # print('Count: ' + str(index))
                # print(paper)

        OperationParameter.set('last_zora_pull', new_last_zora_pull)

    # TODO: Handle error cases (multiple db entries found, no entries found, etc.)
    def import_legacy_annotations(self, file_path):
        with open(file_path, 'rt') as file:
            paper_dict_list = json.load(file)
        for index, paper_dict in enumerate(paper_dict_list):

            # Check if the paper already exists in the database. If it does, we only want to set the sustainable and
            # annotated values (since we can assume that the other existing values are more recent). Otherwise we
            # create a new entry in the database.
            paper = self.db.session.query(Paper).get(paper_dict['uid'])
            if paper:
                paper.sustainable = paper_dict['sustainable']
                paper.annotated = paper_dict['annotated']
            else:
                paper = Paper.create_or_update(paper_dict)
                self.db.session.add(paper)

            # if is_debug():
                # print('Count: ' + str(index))
                # print(paper)
        self.db.session.commit()

        print('Legacy annotations imported')

    # This method handles changes to the settings.
    # zora_pull_interval:   Reschedules the zora_pull_job with the new interval
    # zora_url:             Creates a new connection to the ZORA API with the new URL
    def handle_setting_change(self, target, value, oldvalue, initiator):
        setting_name = target.name

        if setting_name == 'zora_pull_interval':

            # Change the interval of the zora api job
            job = self.scheduler.get_job(id=ServerLogic.ZORA_API_JOB_ID)
            if job:
                job.reschedule(trigger='interval', days=value)
        elif setting_name == 'zora_url':

            # Create a new connection with the new url
            self.zoraAPI = self.zoraAPI = ZoraAPI(value)

        if is_debug():
            print('Setting "' + setting_name + '" was changed to ' + str(value) + '.')

    def create_new_model(self):

        # Reset the machine learning model
        self.ml_tool = MLTool()

        # Get the relevant papers needed for the training
        training_data_set = pd.read_sql_query(self.db.session.query(Paper).filter(Paper.annotated == True).statement,
                                              self.db.session.bind)

        # Prepare the data that is needed for the training and train the classifier
        training_data_set['data'] = training_data_set["title"] + " | " + training_data_set["description"]
        training_data = training_data_set.data
        labels = training_data_set.sustainable
        self.ml_tool.train_classifier(training_data, labels)

        # Update all classifications
        data_set = pd.read_sql_query(self.db.session.query(Paper).filter(Paper.annotated == False).statement,
                                     self.db.session.bind)
        data_set['data'] = data_set["title"] + " | " + data_set["description"]
        data_set['label'] = self.ml_tool.classify(data_set.data)

        for index, row in data_set.iterrows():
            paper = self.db.session.query(Paper).get(row['uid'])
            paper.sustainable = row['label']
        self.db.session.commit()
