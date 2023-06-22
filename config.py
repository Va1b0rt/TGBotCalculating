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
