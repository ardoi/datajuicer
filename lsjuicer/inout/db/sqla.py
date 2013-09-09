import hashlib
import os

import numpy as n

import PyQt4.QtCore as QC

from sqlalchemy import Column, Integer, String, Float, DateTime, PickleType
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import joinedload

from lsjuicer.inout.db.sqlbase import dbmaster
from lsjuicer.static.constants import ImageStates
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.inout.readers.OMEXMLReader import LSMReader, OIBReader, VTITIFReader

class ReaderFactory(object):
    readers = {('LSM','lsm'):LSMReader, ('OIB','oib'):OIBReader, ('OIF','oif'):OIBReader, ('TIF','tif'):VTITIFReader}
    @staticmethod
    def get_reader(filename):
        extension = os.path.splitext(filename)[-1].split('.')[-1]
        for key in ReaderFactory.readers:
            if extension in key:
                reader = ReaderFactory.readers[key]
                return reader
        return None

class ImageMaker(object):
    @staticmethod
    def get_hash(filename):
        if os.path.isfile(filename):
            f = open(filename,'r')
            data = f.read()
            fhash = hashlib.sha1(data).hexdigest()[:10]
            f.close()
            return fhash
        else:
            raise IOError("No such file: %s"%filename)

    @staticmethod
    def check_in_database(filename, session):
        fh = ImageMaker.get_hash(filename)
        print 'using session', session
        try:
            print fh,filename
            query = session.query(MicroscopeImage).filter_by(_file_hash=fh, _file_name = filename)
            #query = session.query(MicroscopeImage).filter_by(_file_hash=fh, _file_name = filename)
            image_from_db = query.one()
            #print 'got from db',image_from_db
            image_from_db.check_for_ome()
            return image_from_db
        except NoResultFound, e:
            print e,fh
            im =  MicroscopeImage(filename, fh)
            session.add(im)
            return im

    def load_image(filename):
        pass

class DBProperty(object):
    def __repr__(self):
        return "<%s>::%s"%(self.__class__.__name__, self.name)



class Project(dbmaster.Base, DBProperty):
    """Project for which experiment was performed"""
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True, nullable=False)
    description = Column(String())
    def __repr__(self):
        return "<Project>::%s"%self.name

class Preparation(dbmaster.Base, DBProperty):
    """Cell type used (but can be also other kinds of preparations)"""
    __tablename__ = "preparations"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique = True, nullable=False)
    description = Column(String())

class Solution(dbmaster.Base, DBProperty):
    """Solution in which experiment was performed"""
    __tablename__ = "solutions"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True, nullable=False)
    description = Column(String())

class Protocol(dbmaster.Base, DBProperty):
    """Experimental protocol during imaging"""
    __tablename__ = "protocols"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True, nullable=False)
    description = Column(String())

class ExperimentalInfo(dbmaster.Base):
    __tablename__ = "exp_info"
    id = Column(Integer, primary_key=True)

    #_image_id = Column(Integer, ForeignKey("images.id"))
    #_image = relationship("MicroscopeImage", backref=backref("exp_info", order_by=id), uselist=False)

    #DB linked experiment properties
    _project_id = Column(Integer, ForeignKey("projects.id"))
    _project = relationship("Project", backref=backref("results", order_by = id))

    _preparation_id = Column(Integer, ForeignKey("preparations.id"))
    _preparation = relationship("Preparation", backref=backref("results", order_by = id))

    _solution_id = Column(Integer, ForeignKey("solutions.id"))
    _solution = relationship("Solution", backref=backref("results", order_by = id))

    _protocol_id = Column(Integer, ForeignKey("protocols.id"))
    _protocol = relationship("Protocol", backref=backref("results", order_by = id))

    #non DB linked attributes
    _sample= Column(Integer)#Coverslip
    _cell = Column(Integer)#Index of measured cell in coverslip
    _comment = Column(String())

    ###########
    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, val):
        self._project = val

    @property
    def preparation(self):
        return self._preparation

    @preparation.setter
    def preparation(self, val):
        self._preparation = val

    @property
    def solution(self):
        return self._solution

    @solution.setter
    def solution(self, val):
        self._solution = val
    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, val):
        self._protocol = val

    #simple properties
    @property
    def sample(self):
        """Number of sample (e.g., the coverslip).\n0 is assumed to mean no assigned value"""
        return self._sample

    @sample.setter
    def sample(self, value):
        print 'setting sample',value
        self._sample = value

    @property
    def cell(self):
        """Cell number in the sample.\n0 is assumed to mean no assigned value"""
        return self._cell

    @cell.setter
    def cell(self, value):
        print 'setting cell',value
        self._cell = value

    @property
    def comment(self):
        """Optional comment"""
        return self._comment

    @comment.setter
    def comment(self, value):
        print 'setting comment',value
        self._comment = value

class Analysis(dbmaster.Base):
    """Analysis performed on file"""
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    date = Column(DateTime)
    imagefile_id = Column(Integer, ForeignKey('images.id'))
    imagefile = relationship("Image", backref=backref('analyses', order_by=id))
    __mapper_args__ = { 'polymorphic_identity':'analysis', 'polymorphic_on':type}

class SparkAnalysis(Analysis):
    __tablename__ = "spark_analyses"
    id = Column(Integer, ForeignKey('analyses.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'spark_analysis'
    }
    def __str__(self):
        return "%i sparks"%(sum([el.spark_count() for el in self.searchregions]))

class TransientAnalysis(Analysis):
    __tablename__ = "transient_analyses"
    id = Column(Integer, ForeignKey('analyses.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'transient_analysis'
    }

class PixelByPixelAnalysis(Analysis):
    __tablename__ = "pixelbypixel_analyses"
    id = Column(Integer, ForeignKey('analyses.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'pixelbypixel_analysis'
    }
    def __str__(self):
        return "%i regions"%(len(self.fitregions))

class PixelByPixelFitRegion(dbmaster.Base):
    __tablename__  = "pixelbypixelfit_regions"

    id = Column(Integer, primary_key=True)

    analysis_id = Column(Integer, ForeignKey('pixelbypixel_analyses.id'))
    analysis = relationship("PixelByPixelAnalysis", backref=backref('fitregions', cascade='all, delete, delete-orphan', order_by=id))

    #Region coordinates
    # x0,y0 .........
    #   .   .       .
    #   .       .   .
    #   ..........x1,y1
    x0 = Column(Integer)
    x1 = Column(Integer)
    y0 = Column(Integer)
    y1 = Column(Integer)

    start_frame = Column(Integer)
    end_frame = Column(Integer)

    def set_coords(self, coords):
        self.x0 = coords[0]
        self.x1 = coords[1]
        self.y0 = coords[2]
        self.y1 = coords[3]

    @property
    def width(self):
        return abs(self.x1 - self.x0)# * self.analysis.imagefile.delta_time

    @property
    def height(self):
        return abs(self.y1 - self.y0)# * self.analysis.imagefile.delta_space

    @property
    def frames(self):
        return self.end_frame - self.start_frame# * self.analysis.imagefile.delta_space

class PixelByPixelRegionFitResult(dbmaster.Base):
    __tablename__  = "pixelbypixelfitregion_results"
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey("pixelbypixelfit_regions.id"))
    region = relationship("PixelByPixelFitRegion", backref=backref("results", cascade='all, delete, delete-orphan'), order_by=id)
    fit_settings = Column(PickleType)

    def get_fitted_pixel(self, x, y):
        session = dbmaster.object_session(self)
        new_session = False
        if not session:
            session = dbmaster.get_session()
            new_session = True
        try:
            pixel = session.query(FittedPixel).options(joinedload(FittedPixel.pixel_events)).\
                    filter(FittedPixel.result==self).\
                    filter(FittedPixel.x==int(x)).\
                    filter(FittedPixel.y==int(y)).one()
            ret = pixel
        except NoResultFound:
            ret = None
        if new_session:
            session.expunge(ret)
            session.close()
        return ret

class FittedPixel(dbmaster.Base):
    __tablename__ = "fitted_pixels"
    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey("pixelbypixelfitregion_results.id"))
    result = relationship("PixelByPixelRegionFitResult", backref=backref("pixels", cascade='all, delete, delete-orphan'), order_by=id)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    #event_count = Column(Integer, nullable=False)
    baseline = Column(PickleType)

    @property
    def event_count(self):
        return len(self.pixel_events)

class PixelEvent(dbmaster.Base):
    __tablename__ = "pixel_events"
    id = Column(Integer, primary_key=True)
    pixel_id = Column(Integer, ForeignKey("fitted_pixels.id"))
    pixel = relationship("FittedPixel", backref=backref("pixel_events", cascade='all, delete, delete-orphan'), order_by=id)

    event_id = Column(Integer, ForeignKey("events.id"))
    event = relationship("Event", backref=backref("pixel_events", cascade='all, delete, delete-orphan'), order_by=id)
    parameters = Column(PickleType)


class Event(dbmaster.Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey("pixelbypixelfitregion_results.id"))
    result = relationship("PixelByPixelRegionFitResult", backref=backref("events", cascade='all, delete, delete-orphan'), order_by=id)
    category_id = Column(Integer, ForeignKey("event_categories.id"))
    category = relationship("EventCategory", backref=backref("events", cascade='all, delete, delete-orphan'), order_by=id)

class EventCategory(dbmaster.Base):
    __tablename__ = "event_categories"
    id = Column(Integer, primary_key=True)
    category_type_id = Column(Integer, ForeignKey("event_category_types.id"))
    category_type = relationship("EventCategoryType")
    eps = Column(Float)
    min_samples = Column(Integer)
    description = Column(String)

    def __str__(self):
        return "min samples={}, eps={:.2f}".format(self.min_samples, self.eps)

class EventCategoryType(dbmaster.Base):
    __tablename__ = "event_category_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    category_type = Column(String)
    __mapper_args__ = { 'polymorphic_identity':'event_category_type', 'polymorphic_on':category_type}

class EventCategoryLocationType(EventCategoryType):
    """Category of events based on their location"""
    __tablename__ = "event_category_location_types"
    id = Column(ForeignKey("event_category_types.id"), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'location'
    }

class EventCategoryShapeType(EventCategoryType):
    """Category of events based on their shape"""
    __tablename__ = "event_category_shape_types"
    id = Column(ForeignKey("event_category_types.id"), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'shape'
    }

class SearchRegion(dbmaster.Base):
    """Search region for SparkDetect"""
    __tablename__ = "search_regions"
    __mapper_args__ = {'column_prefix':'_'}
    id = Column(Integer, primary_key=True)

    analysis_id = Column(Integer, ForeignKey('spark_analyses.id'))
    analysis = relationship("SparkAnalysis", backref=backref('searchregions', order_by=id))

    #Region coordinates
    # x0,y0 .........
    #   .   .       .
    #   .       .   .
    #   ..........x1,y1
    x0 = Column(Integer)
    x1 = Column(Integer)
    y0 = Column(Integer)
    y1 = Column(Integer)

    @property
    def width(self):
        return abs(self.x1 - self.x0) * self.analysis.imagefile.delta_time

    @property
    def height(self):
        return abs(self.y1 - self.y0) * self.analysis.imagefile.delta_space

    def set_coords(self, coords):
        self._x0 = coords[0]
        self._x1 = coords[1]
        self._y0 = coords[2]
        self._y1 = coords[3]

    def spark_count(self):
        return len(self.sparks)

    def __repr__(self):
        return "coords=%i %i %i %i"%(self._x0, self._x1,self._y0, self._y1)

    def check_coords(self, coords):
        my_coords = [self._x0, self._x1, self._y0, self._y1]
        return coords == my_coords

class Spark(dbmaster.Base):
    __tablename__ = "sparks"
    id = Column(Integer, primary_key=True)

    region_id = Column(Integer, ForeignKey('search_regions.id'))
    region = relationship("SearchRegion", backref=backref('sparks', order_by=id))

    fwhm = Column(Float)
    fdhm = Column(Float)
    val_at_max = Column(Float)
    time_at_max = Column(Float)
    loc_at_max = Column(Float)
    baseline = Column(Float)
    decay_constant = Column(Float)
    risetime = Column(Float)

    temporal_fit_params = Column(PickleType)
    spatial_fit_params = Column(PickleType)
    temporal_fit_fun = Column(String) #names of fitting functions
    spatial_fit_fun = Column(String)

    x0 = Column(Integer)
    x1 = Column(Integer)
    y0 = Column(Integer)
    y1 = Column(Integer)

    def set_coords(self, coords):

        self.x0 = int(coords[0])
        self.x1 = int(coords[1])
        self.y0 = int(coords[2])
        self.y1 = int(coords[3])
    def get_qrectf(self):
        topleft =  QC.QPointF(self.x0, self.y0)
        bottomright =  QC.QPointF(self.x1, self.y1)
        return QC.QRectF(topleft, bottomright)

class Image(dbmaster.Base):
    """Base image class"""
    __tablename__= "images"
    id = Column(Integer, primary_key=True)
    type = Column(String(50))

    _image_width = Column(Integer)
    _image_height = Column(Integer)
    _image_frames = Column(Integer)
    _delta_time = Column(Float)
    _record_date = Column(DateTime)
    _description = Column(String())
    _delta_space = Column(Float)
    _channels = Column(Integer)
    _state = Column(Integer, nullable = False)
    _comment = Column(String())

    _exp_info_id = Column(Integer, ForeignKey("exp_info.id"))
    _exp_info = relationship("ExperimentalInfo",
            backref=backref("image", order_by=id), uselist=False)
    __mapper_args__ = { 'polymorphic_identity':'image', 'polymorphic_on':type}

    @property
    def exp_info(self):
        return self._exp_info

    @exp_info.setter
    def exp_info(self, val):
        self._exp_info = val

    @property
    def channels(self):
        return self._channels

    @channels.setter
    def channels(self, value):
        print 'setting channels to',value
        assert value >= 1, "Number of channels cannot be less than 1. %i given"%value
        self._channels = value


    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self._comment = value

    @property
    def image_width(self):
        return self._image_width

    @image_width.setter
    def image_width(self, width):
        self._image_width = width

    @property
    def image_height(self):
        return self._image_height

    @image_height.setter
    def image_height(self, height):
        self._image_height = height

    @property
    def image_frames(self):
        return self._image_frames

    @image_frames.setter
    def image_frames(self, frames):
        self._image_frames = frames

    @property
    def delta_time(self):
        return self._delta_time

    @delta_time.setter
    def delta_time(self, value):
        self._delta_time = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, desc):
        self._description = desc

    @property
    def record_date(self):
        return self._record_date

    @record_date.setter
    def record_date(self, date):
        self._record_date = date
    @property
    def delta_space(self):
        return self._delta_space

    @delta_space.setter
    def delta_space(self, value):
        self._delta_space = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    #non db properties
    @property
    def timestamps(self):
        print 'timestamp'
        #print self
        return self.ome_file.timestamps
    @property
    def event_times(self):
        print 'events'
        #print self
        return self.ome_file.event_times

    def __init__(self):
        dbmaster.Base.__init__(self)
        self._state = None


class PixelFittedSyntheticImage(Image):
    """Image built from a PixelByPixelRegionFitResult"""
    __tablename__ = "pixelfitted_synthentic_images"
    id = Column(Integer, ForeignKey('images.id'), primary_key=True)
    result_id = Column(Integer, ForeignKey("pixelbypixelfitregion_results.id"))
    result = relationship("PixelByPixelRegionFitResult", backref=backref("synthetic_images"))
    __mapper_args__ = {
        'polymorphic_identity':'pixelfitted_synthetic_image'
    }
    def __init__(self, pixelfitresult):
        Image.__init__(self)
        reg = pixelfitresult.region
        self.image_width = reg.width - 2*pixelfitresult.fit_settings['padding']
        self.image_height = reg.height - 2*pixelfitresult.fit_settings['padding']
        self.channels = 2
        self.image_frames = reg.frames
        analysis = reg.analysis
        self.record_date = analysis.date
        mimage = analysis.imagefile
        self.exp_info = mimage.exp_info
        self.delta_time = mimage.delta_time
        self.delta_space = mimage.delta_space
        self.file_name = os.path.basename(mimage.file_name) + ":fitres %i"%pixelfitresult.id
        self.file_hash = mimage.file_hash
        self.state = mimage.state
        self.description = ""

        results = {}
        results['width'] = self.image_width
        results['height'] = self.image_height
        results['frames'] = self.image_frames
        results['dx'] = pixelfitresult.fit_settings['padding']
        results['dy'] = pixelfitresult.fit_settings['padding']
        results['x0'] = reg.x0
        results['y0'] = reg.y0
        results['fits'] = pixelfitresult.pixels
        self.results = results


    def image_data(self, a=None):
        new_data = tf.clean_plot_data(self.results)
        bl = tf.clean_plot_data(self.results, only_bl = True)
        shape = [1]
        shape.extend(new_data.shape)
        new_data.shape = shape
        bl.shape = shape
        out = n.vstack((new_data, bl))
        return out

    def get_pixel_size(self, im_type):
        return n.array((1.0,1.0))

class MicroscopeImage(Image):
    """Representation of image recorded by the microscope"""
    __tablename__ = "microscope_images"
    id = Column(Integer, ForeignKey('images.id'), primary_key=True)
    #ome_dir = os.path.join(os.getenv('HOME'), '.JuicerTemp')
    id = Column(Integer, ForeignKey('images.id'), primary_key=True)
    _file_hash = Column(String(200), nullable=False)#, unique=True)
    _file_name = Column(String(500), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity':'microscope_image'
    }

    @property
    def ome_dir(self):
        return dbmaster.get_config_setting_value('ome_folder')

    @property
    def file_hash(self):
        """hash of original image file"""
        return self._file_hash

    @file_hash.setter
    def file_hash(self, fhash):
        self._file_hash = fhash

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, name):
        self._file_name = name

    @property
    def ome_name(self):
        #return self.file_hash+".ome.tiff"
        return self.file_hash+".ome"

    @property
    def ome_full_name(self):
        return os.path.join(self.ome_dir, self.ome_name)

    def __init__(self, file_name, file_hash):
        Image.__init__(self)
        self.file_name = file_name
        #what if there are two identical files with different names?
        self.file_hash = file_hash
        self.check_for_ome()
        self.exp_info = ExperimentalInfo()


    def check_for_ome(self):
        print "Check for ome", self.ome_full_name
        if os.path.isfile(self.ome_full_name):
            print 'Ome file %s found for image %s'%(self.ome_name, self.file_name)
            reader = ReaderFactory.get_reader(self.file_name)
            self.ome_file = reader(self.ome_full_name)
            if self.state == ImageStates.NOT_CONVERTED or self.state is None:
                self.ome_file.read_meta()
                self.state = ImageStates.CONVERTED
                self.populate_attributes()
            #dd = self.ome_file.get_image_data("Pixels")
        else:
            print 'No OME file %s found for image %s'%(self.ome_name, self.file_name)
            self.state = ImageStates.NOT_CONVERTED
            self.ome_file = None
        return

    def image_data(self, image_type):
        if self.ome_file:
            self.ome_file.read_image(image_type)
            return self.ome_file.images[image_type]#["ImageData"]
        else:
            return None

    def populate_attributes(self):
        of = self.ome_file
        of.read_meta()
        self.delta_space = of.image_step_y
        #print "populate",of.interval
        self.delta_time = of.interval
        self.record_date = of.datetime
        self.image_width = of.image_width
        self.image_height = of.image_height
        self.image_frames = of.frames
        self.channels = of.channels
        self.description = of.description

    def set_conversion_failed(self):
        self.state = ImageStates.CONVERSION_FAILED

    def get_pixel_size(self, im_type):
        #im type either "Reference" or "Pixels"
        if self.ome_file:
            of = self.ome_file
            try:
                if im_type == "Reference":
                    delta_axis1 = float(of.images[im_type]["PixelAttributes"]["PhysicalSizeX"])
                else:
                    #if we have a timescan then delta x is line interval
                    delta_axis1 = self.delta_time
                delta_axis2 = float(of.images[im_type]["PixelAttributes"]["PhysicalSizeY"])
                return n.array((delta_axis1, delta_axis2))
            except KeyError:
                print "keyerror in get_pixel_size"
                return n.array((1.0,1.0))
        else:
            return None

    def __repr__(self):
        #try:
        if 1:
            stuff = (self.file_name, self.file_hash,
                self.image_width, self.image_height, str(self.record_date),
                self.delta_space, self.delta_time, self.state, self.channels)
            out = []
            for k in stuff:
                if k is None:
                    out.append("None")
                else:
                    out.append(str(k))
            str_repr = ", ".join(out)

            rstr =  "::MicroscopeImage:: %s"%str_repr        #except TypeError:
        #    rstr = "::MicroscopeImage:: %s not in DB nor converted"%(self.file_name)
        return rstr
