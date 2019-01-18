from flaskr import app
from flask import jsonify

@app.route('/data/papers/<parameters>')
def getPapers(parameters):
    papers = [{'uid': '1234', 'name': 'paper1', 'abstract': 'asfaskföasdfkö'},
              {'uid': '3456', 'name': 'paper2', 'abstract': parameters}]
    return jsonify(papers)

# TODO: Add Rest
#@flaskr.route('/data/papers/<parameters>', methods=['GET', 'POST'])
