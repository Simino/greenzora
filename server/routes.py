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




# TODO: Add Rest
#@server.route('/data/papers/<parameters>', methods=['GET', 'POST'])
