
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, PickleType
from sqlalchemy.orm.exc import NoResultFound

from lsjuicer.util import logger, config

class DBMaster(object):

    def __init__(self):
        self.logger = logger.get_logger(__name__)
        self.logger.info("starting DBMaster")
        self.Base = declarative_base()
        self.logger.info("DB file at:{}".format(config.db_file))
        self.engine = create_engine('sqlite:///{}'.format(config.db_file), echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.tables_checked = False
        self.session = None
        #self.default_configuration()

    def default_configuration(self, override = False):
        default = {
            "visualization_options_reference":
                {"blur": 1.3,
                "colormap": "gist_heat",
                "saturation": 5,
                'colormap_reverse': False},
            #
            "filetype": "oib",
        }
        default.update(config.folders)

        for key in default:
            try:
                val= self.get_config_setting_value(key)
            except:
                val = None
            if val and not override:
                print "config value: %s=%s" % (key, str(val))
                continue
            else:
                print "setting default config value: %s=%s"\
                    % (key, str(default[key]))
                self.set_config_setting(key, default[key])


    def make_tables(self):
        session = self.Session()
        engine = session.get_bind()
        self.Base.metadata.create_all(engine)

    def check_tables(self, force=False):
        if not self.tables_checked or force:
            #tables in database
            insp = reflection.Inspector.from_engine(self.engine)
            table_names_db = insp.get_table_names()
            #tables in metadata
            table_names_md = self.Base.metadata.tables.keys()
            missing = []
            for table_name in table_names_md:
                if table_name not in table_names_db:
                    missing.append(table_name)
            if missing:
                self.logger.info('Tables {} missing. Adding to database'.format(str(missing)))
                self.make_tables()
            self.tables_checked = True

    def get_session(self):
        if self.session:
            return self.session
        else:
            self.check_tables()
            self.session = self.Session()
            # print 'created session', session
            return self.session

    def commit_session(self):
        try:
            self.session.commit()
            return True
        except IntegrityError as e:
            self.logger.error(str(e))
            self.logger.error('rolling back')
            self.session.rollback()
            return False

    def end_session(self):
        self.logger.info("ending session {}".format(self.session))
        try:
            self.session.commit()
            self.session.close()
            self.session = None
            return True
        except IntegrityError as e:
            self.logger.error(str(e))
            self.logger.error('rolling back')
            self.session.rollback()
            return False

    def object_session(self, obj):
        try:
            session = self.Session.object_session(obj)
            return session
        except:
            return None

    def object_to_session(self, obj):
        session = self.object_session(obj)
        if not session:
            session = self.get_session()
            session.add(obj)
        return session

    def get_config_setting(self, name, session):
        try:
            setting = session.query(
                ConfigurationSetting).filter_by(name=name).one()
            return setting
        except NoResultFound:
            return None

    def get_config_setting_value(self, name):
        session = self.get_session()
        setting = self.get_config_setting(name, session)
        if setting:
            return setting.value
        else:
            return None

    def set_config_setting(self, name, value):
        session = self.get_session()
        setting = self.get_config_setting(name, session)
        if setting:
            setting.value = value
        else:
            setting = ConfigurationSetting()
            setting.name = name
            setting.value = value
            session.add(setting)
        self.commit_session()

dbmaster = DBMaster()

class ConfigurationSetting(dbmaster.Base):
    __tablename__ = "configuration"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    value = Column(PickleType)

dbmaster.default_configuration()
