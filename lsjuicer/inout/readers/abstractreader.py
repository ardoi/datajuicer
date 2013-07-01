from lsjuicer.static.constants import Constants


class AbstractReader(object):
    def get_image_data(self, image_type = "Pixels"):
        if not self.images[image_type]["ImageData"]:
            self.read_image(image_type)
        return self.images[image_type]["ImageData"]

    def __init__(self, filename):
        self.state = Constants.INSPECTED
        self.state_text = {Constants.NOT_INSPECTED:"File not converted. Press convert button",
                Constants.INSPECTION_FAILED:"Error reading file. Check log for details",
                #Constants.INSPECTED:"File OK. No recording notes in file",
                #Constants.PLOTTED:"File OK. No recording notes in file"}
                Constants.INSPECTED:"",
                Constants.PLOTTED:""}
        self.image_in = False
        self.filename = filename
        self.timestamps = None
        self.event_times = None
        self.info_txt = ''
        #self.image_width = None
        #self.image_height = None
        self.im_data = None
        self.interval =  None
        self.datetime = None
        self.loadable = True
        self.data_loaded = False
        self.metadata_loaded = False
        self.im_data = {}
        #self.channels = None
        self.notes=''
        #self.read()

    #def has_timestamps(self):
    #    if len(self.timestamps)>0:
    #        return True
    #    else:
    #        return False

    #def has_events(self):
    #    if len(self.event_times)>0:
    #        return True
    #    else:
    #        return False
