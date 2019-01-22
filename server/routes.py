from flask import jsonify
from server import server_app, db, models


@server_app.route('/data/papers/<parameters>')
def get_papers(parameters):
    # TODO: Load papers from database
    papers = [{'uid': '1234', 'name': 'paper1', 'abstract': 'asfaskföasdfkö'},
              {'uid': '3456', 'name': 'paper2', 'abstract': parameters}]
    return jsonify(papers)


@server_app.route('/data/papers/<parameters>')
def get_statistics(parameters):
    # TODO: Get statistics from database
    statistics = []
    return jsonify(statistics)


@server_app.route('/annotation')
def get_annotation():
    # TODO: Get scientific paper that has not yet been classified from ZORA and store that information somewhere
    annotation = {}
    return jsonify(annotation)


@server_app.route('/annotation/<uid>/<classification>', methods=['POST'])
def classify(uid, classification):
    db.session.add(models.Paper(uid=uid, sustainable=classification))
    db.session.commit()


@server_app.route('/settings')
def get_settings():
    # TODO: Get settings from the database
    settings = {}
    return jsonify(settings)


@server_app.route('/settings/<parameters>', methods=['POST'])
def set_settings(parameters):
    settings_dict = parse_parameters(parameters)
    for key, value in settings_dict.items():
        setting = models.Setting.query.filter_by(name=key)
        setting.value = value
    db.session.commit()
    return jsonify(load_settings())

# TODO: Add Rest
#@server.route('/data/papers/<parameters>', methods=['GET', 'POST'])


# ------------ HELPER FUNCTIONS ---------------

# Parses the comma separated parameters (URL/a=b,c=d...) into a dictionary ({a: b, c: d, ...})
def parse_parameters(parameters):
    parameter_dictionary = {}
    parameter_list = parameters.split(',')
    for parameter in parameter_list:
        name, value = parameter.split('=')
        parameter_dictionary[name] = value
    return parameter_dictionary


# Get the settings from the database as a dictionary ({name: value, name: value, ...)
def load_settings():
    setting_dictionary = {}
    settings = models.Setting.query.all()
    for setting in settings:
        name = setting.name
        value = setting.value
        setting_dictionary[name] = value
    return setting_dictionary