print "DEPRECATED: USE yaml files in config directory"

# CPP Code parses config.py as text, so the dict name doesn't matter
deprecated = {
    'mysql_log_server': 'localhost',
    'mysql_log_user': 'rhUser',
    'mysql_log_password': 'waterloo',
    'mysql_log_db': 'RobotHouseDemoDB',
    'mysql_log_table': 'SensorLog',
}
