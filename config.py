import datetime
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

BOT_API_TOKEN = config.get('TELEGRAM', 'BOT_API_TOKEN')


# LOGGING
level = config.get('LOGGING', 'level')
log_path = config.get('LOGGING', 'log_path').replace('rename_this', datetime.datetime.now().strftime("%d.%m.%Y"))
log_format = config.get('LOGGING', 'log_format')
rotation = config.get('LOGGING', 'rotation')
compression = config.get('LOGGING', 'compression')


# GOOGLE
keyfile = config.get('GOOGLE', 'keyfile')
sheet_url = config.get('GOOGLE', 'sheet_url')
worksheet = config.get('GOOGLE', 'worksheet')
workers_sheet = config.get('GOOGLE', 'workers_sheet')
workers_worksheet = config.get('GOOGLE', 'workers_worksheet')
statement_columns = config.get('GOOGLE', 'statement_columns')
statement_worksheet = config.get('GOOGLE', 'statement_worksheet')


# DataBase
db_host = config.get('DataBase', 'db_host')
db_user = config.get('DataBase', 'db_user')
db_passwd = config.get('DataBase', 'db_passwd')
database = config.get('DataBase', 'database')
db_port = config.getint('DataBase', 'db_port')
