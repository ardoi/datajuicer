from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, PickleType
from sqlalchemy.orm.exc import NoResultFound


class DBMaster(object):

    def __init__(self):
        print "starting DBMaster"
        self.Base = declarative_base()
        self.engine = create_engine('sqlite:///tables.db', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.tables_created = False

    def make_tables(self):
        print "making tables"
        if not self.tables_created:
            session = self.Session()
            engine = session.get_bind()
            self.Base.metadata.create_all(engine)

    def check_tables(self):
        if not self.tables_created:
            insp = reflection.Inspector.from_engine(self.engine)
            table_names = insp.get_table_names()
            print 'tables:', table_names
            if not table_names:
                self.make_tables()
                insp = reflection.Inspector.from_engine(self.engine)
                table_names = insp.get_table_names()
            print 'tables:', table_names
            self.tables_created = True

    def get_session(self):
        self.check_tables()
        session = self.Session()
        # print 'created session', session
        return session

    def end_session(self, session):
        # print "ending session", session
        try:
            session.commit()
            session.close()
            return True
        except IntegrityError as e:
            print e
            print 'rolling back'
            session.rollback()
            return False

    def object_session(self, obj):
        try:
            session = self.Session.object_session(obj)
            # print 'session is',session
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
        session.close()
        # print 'getting value',name
        if setting:
            # print 'value is',setting.value
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
        self.end_session(session)


dbmaster = DBMaster()


class ConfigurationSetting(dbmaster.Base):
    __tablename__ = "configuration"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    value = Column(PickleType)
