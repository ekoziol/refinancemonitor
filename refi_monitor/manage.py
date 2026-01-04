from app import init_app
from flask_migrate import MigrateCommand, Manager

manager = Manager(create_app)
manager.add_option("-c", "--config", dest="config_module", required=False)
manager.add_command('db', MigrateCommand)
