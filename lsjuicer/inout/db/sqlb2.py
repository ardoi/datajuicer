import datetime
import traceback

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, DateTime, PickleType,Boolean
from sqlalchemy.exc import OperationalError

class DBMaster(object):
    def __init__(self):
        print "starting DBMaster2"
        self.fname = "tables2.db"
        self.Base = declarative_base()
        self.engine = create_engine('sqlite:///%s'%self.fname, echo=False,
                echo_pool=True, connect_args={'timeout': 30})
        self.Session = sessionmaker(bind = self.engine)
        #self.make_tables()
        self.tables_created = False

    def reset_tables(self):
        self.tables_created = False
        print 'reset'
        connection = self.engine.connect()
        trans = connection.begin()
        for name, table in self.Base.metadata.tables.items():
            print 'delete',name,table.delete()
            try:
                connection.execute(table.delete())
            except OperationalError:
                pass
                #traceback.print_exc()
        connection.execute("VACUUM")
        trans.commit()
        trans.close()
        connection.close()

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
            print 'tables:',table_names
            self.tables_created = True


    def get_session(self):
        self.check_tables()
        session = self.Session()
        #print 'created session', session
        return session

    def end_session(self, session):
        #print "ending session", session
        try:
            session.commit()
            session.close()
            return True
        except IntegrityError as e:
            print e
            print 'rolling back'
            session.rollback()
            return False

dbmaster = DBMaster()

class Job(dbmaster.Base):

    __tablename__ = "job"
    id = Column(Integer, primary_key=True)
    params = Column(PickleType)
    worker_id = Column(Integer)#, ForeignKey("worker.id")
    #worker_id = Column(Integer, ForeignKey("worker.id")
    #worker = relationship("Worker", backref=backref("jobs", order_by = id))
    result = Column(PickleType)
    finished = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    failed = Column(Boolean)
    timed_out = Column(Boolean)
    running = Column(Boolean)

    def __init__(self):
        self.finished  = False
        self.failed = False
        self.timed_out = False
        self.running = False

    #def __repr__(self):
    #    return "<Job id=%i,worker=%i,running=%i,failed=%i,finished=%i,timed_out=%i>"\
    #            %(self.id,self.worker_id,self.running, self.failed,self.finished,self.timed_out)

    @property
    def run_time(self):
        if self.end_time and self.start_time:
            return (self.end_time-self.start_time).total_seconds()
    @property
    def done(self):
        return self.finished or self.failed or self.timed_out

class Worker(dbmaster.Base):
    __tablename__ = "worker"
    id = Column(Integer, primary_key=True,autoincrement = False)
    #wid = Column(Integer)
    running = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    job_start_time = Column(DateTime)
    job_end_time = Column(DateTime)
    finished = Column(Boolean)
    running_job = Column(Integer)

    def __init__(self):
        self.finished  = False
        self.running = False

    @property
    def run_time(self):
        dt = self.end_time - self.start_time
        return dt.total_seconds()

    @property
    def job_run_time(self):
        #print self.id, self.job_start_time,
        if self.job_start_time:
            if self.job_end_time:
                dt = self.job_end_time - self.job_start_time
            else:
                dt = datetime.datetime.now() - self.job_start_time
            #print self.id, dt.total_seconds()
            return dt.total_seconds()
        else:
            return 0.0
