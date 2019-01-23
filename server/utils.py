from server import server_app
from datetime import datetime


def is_debug():
    return server_app.config['DEBUG']


# Parses the value of a Setting or OperationParameter object to the corresponding type
def parse_db_value(db_object):
    value = db_object.value
    value_type = db_object.type.name
    if value_type == 'int':
        return int(value)
    if value_type == 'datetime':
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
