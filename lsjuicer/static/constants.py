class Constants:
    TRANSIENT_TYPE = 100
    SPARK_TYPE = 101
    SPARKDETECT_TYPE = 102
    DUMMY_TYPE = 99

    NOT_INSPECTED = 0
    INSPECTION_FAILED = -1
    INSPECTED = 1
    PLOTTED = 2

    ROI = 1
    BGROI = 2
    GROUP = 3

    MANUAL = 33
    AUTOMATIC = 34

    move = 10
    resize_br = 11
    resize_bl = 12
    resize_tl = 13
    resize_tr = 14
    resize_l = 15
    resize_r = 16
    resize_t = 17
    resize_b = 18

    EVENTS = 20
    GAPS = 21


class ImageStates:
    NOT_CONVERTED = 1
    CONVERTED = 2
    CONVERSION_FAILED = 3
    ANALYZED_IN_PREVIOUS_SESSION = 4
    ANALYZED_IN_CURRENT_SESSION = 5


class ImageSelectionTypeNames:
    ROI = 'ROI'
    SPARK_ROI = 'Spark_ROI'
    BACKGROUND = 'Background'
    LINE = "Line"
    F0 = 'F0'
    TIMERANGE = "time_range"
    SPARK_TYPE = 101


class TransientBoundarySelectionTypeNames:
    AUTO = 'Auto'
    MANUAL = 'Manual'
    SPARK = 'Spark'


class TransientTabState:
    # states = 0
    FRESH = 0

    SEARCHING = 1

    AUTO = 12
    MANUAL = 11

    NOREGIONS = 101
    REGIONS = 102
    TRANSIENTSSHOWING = 103

    APPROVED = 2
    APPROVEDANDSEARCHING = 3

    # index numbers
    TRANSIENTS = 0
    SELECTIONMODE = 1
    SELECTION = 2

    TRANSIENTS_NONE = 0
    TRANSIENTS_VISIBLE = 1
    TRANSIENTS_HIDDEN = 2
    TRANSIENTS_ALL = [0, 1, 2]

    SELECTIONMODE_NONE = 0
    SELECTIONMODE_MANUAL = 1
    SELECTIONMODE_AUTO = 2
    SELECTIONMODE_ALL = [0, 1, 2]

    SELECTION_NONE = 0
    SELECTION_PRESENT = 1
    SELECTION_ALL = [0, 1]

    def __init__(self, parents=None):
#        self.name = name
        self.state_id = TransientTabState.states
        TransientTabState.states += 1
        if isinstance(parents, list):
            self.parents = parents
        else:
            self.parents = [parents]

# class TransientTabStates:
# main states
# Default = TransientTabState() # for any state that has not been specified
#    Fresh = TransientTabState()
#    TransientSearchInProgress = TransientTabState()
#    ApprovedTransientsShowing = TransientTabState()
#    TransientsApproved = TransientTabState()
#
# search states
#    AutoInProgress = TransientTabState(TransientSearchInProgress)
#    ManualInProgress = TransientTabState(TransientSearchInProgress)
#    TransientSearchRegionSelected = TransientTabState(TransientSearchInProgress)
#
#    TempTransientsShowing = TransientTabState(TransientSearchInProgress)
#    TempTransientsShowingManual = TransientTabState(TempTransientsShowing)
#    TempTransientsShowingAuto = TransientTabState(TempTransientsShowing)

# class StateDictionary:
#    def __init__(self, default = False):
#        self.default = False
#        self.d = {}
#
#    def recSet(self, val, args):
#        """Recursively set dict slots to value val. E.g., if args == ('1','2',['3','9'],'4') then
#        d[1][2][3][4] and d[1][2][9][4] will be set to val"""
#        if len(args)>1 and isinstance(args,tuple):
#            if isinstance(args[0],list):
#                r = {}
#                for a in args[0]:
#                    r.update({a:self.recSet(val,args[1:])})
#                return r
#            else:
#                return {args[0]:self.recSet(val,args[1:])}
#        else:
#            if isinstance(args[0],list):
#                r = {}
#                for a in args[0]:
#                    r.update({a:val})
#                return r
#            else:
#                return {args[0]:val}
#
#    def setState(self,val,*args):
#        self.d.update(self.recSet(val,args))
#
#
#    def recGet(self,args,d=None):
#        try:
#            if not d:
#                d=self.d[args[0]]
#            else:
#                d=d[args[0]]
#        except (IndexError, KeyError):
#            return self.default
#        if isinstance(d,dict):
#            return self.recGet(args[1:],d)
#        else:
#            return d
#
#    def get(self,*args):
#        if isinstance(args[0],tuple):
#            args = args[0]
#        return self.recGet(args)
