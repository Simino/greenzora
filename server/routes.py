from flask import jsonify, redirect, url_for, flash, render_template, request
from server import db, server_app, models
from server.models import Paper, ServerSetting, User
from flask_login import current_user, login_user, logout_user
import sqlite3
import jinja2
import server.queryFactory as factory

# ----------------- ROUTES -----------------------

@server_app.route('/')
@server_app.route('/index')
def index():
    alcrows = db.session.query(Paper).filter(Paper.sustainable== True).all()
    rowsQuery= 'SELECT * FROM papers WHERE sustainable = 1'
    rows = factory.query(factory.getCursor('database.db'),rowsQuery)
    return render_template('list.html', rows= alcrows)


@server_app.route('/form')
def form():
    all_sustainable_papers = db.session.query(Paper).filter(Paper.sustainable == True).all()

    all_sustainable_paper_creators = db.session.query(models.PaperCreator).filter(models.PaperCreator.paper_uid.in_([paper.uid for paper in all_sustainable_papers])).all()
    creators = db.session.query(models.Creator).filter(models.Creator.id.in_([c.creator_id for c in all_sustainable_paper_creators])).all()

    all_sustainable_paper_keywords = db.session.query(models.PaperKeyword).filter(models.PaperKeyword.paper_uid.in_([paper.uid for paper in all_sustainable_papers])).all()
    keywords = db.session.query(models.Keyword).filter(models.Keyword.id.in_([k.keyword_id for k in all_sustainable_paper_keywords])).all()

    return render_template('searchlist.html', creators=creators, keywords=keywords)


@server_app.route('/results', methods=['GET', 'POST'])
def results():
    if'creator_select' in request.form:
        creator_select = request.form['creator_select']
        print('creator_select selected')
        print(request.form)
    paperCreators = db.session.query(models.PaperCreator).filter(models.PaperCreator.creator_id == creator_select).all()
    papers = db.session.query(Paper).filter(Paper.uid.in_([p.paper_uid for p in paperCreators])).filter(Paper.sustainable == True).all()

    paperKeywords = db.session.query(models.PaperKeyword).filter(models.PaperKeyword.)
    keywords = db.session.query(models.Keyword.name).filter(models.Keyword.id.in_([k.keyword_id for k in paperKeywords]))
    return render_template('results.html', papers=papers)


@server_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/annotation'))
    form = 'TODO'   # LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('/login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('/annotation'))
    return 'TODO'   # render_template('login.html', title='Sign In', form=form)


@server_app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('/data/papers/'))

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


# TODO handle return
@server_app.route('/annotation/<uid>/<classification>', methods=['POST'])
def classify(uid, classification):
    paper = Paper(uid=uid, sustainable=classification)
    db.session.merge(paper)
    db.session.commit()
    return jsonify('SOMETHING')


@server_app.route('/settings')
def get_settings():
    settings = {}
    return jsonify(settings)


# TODO handle return
@server_app.route('/settings/<parameters>', methods=['POST'])
def set_settings(parameters):
    settings_dict = parse_parameters(parameters)
    for key, value in settings_dict.items():
        setting = ServerSetting(name=key, value=value)
        db.session.merge(setting)
    db.session.commit()
    return jsonify('SOMETHING')

# TODO: Add Rest
#@server.route('/data/papers/<parameters>', methods=['GET', 'POST'])

# ----------------- END ROUTES -----------------------


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
    settings = db.session.query(ServerSetting).all()
    for setting in settings:
        name = setting.name
        value = setting.value
        setting_dictionary[name] = value
    return setting_dictionary

# ------------ END HELPER FUNCTIONS ---------------
