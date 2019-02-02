from flask import jsonify, redirect, url_for, flash
from server import db, server_app
from server.models import Paper, ServerSetting, User
from flask_login import current_user, login_user, logout_user


# ----------------- ROUTES -----------------------

@server_app.route('/login', method=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/annotation'))
    form = 'TODO'   # LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
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
