from lsjuicer.ui.items.selection import SelectionType, SelectionAppearance
from constants import ImageSelectionTypeNames as ISTN
from constants import TransientBoundarySelectionTypeNames as TBSTN

data = {}

# imagetab
selections_0 = []
ROI_appearance = SelectionAppearance()
ROI_appearance.set_line_params('green', 4)
ROI_appearance.set_active_line_params()

BK_appearance = SelectionAppearance()
BK_appearance.set_line_params('red', 4)
BK_appearance.set_active_line_params()

F0_appearance = SelectionAppearance()
F0_appearance.set_line_params('blue', 4)
F0_appearance.set_active_line_params()

selections_0.append(SelectionType(ISTN.ROI, ROI_appearance, 1))
selections_0.append(SelectionType(ISTN.BACKGROUND, BK_appearance, 1))
selections_0.append(SelectionType(ISTN.F0, F0_appearance, 1))
data['imagetab.transients'] = selections_0

selections_00 = []
SPARK_ROI_appearance = SelectionAppearance()
SPARK_ROI_appearance.set_line_params('green', 4)
SPARK_ROI_appearance.set_active_line_params()
selections_00.append(SelectionType(ISTN.SPARK_ROI, SPARK_ROI_appearance, -1))
selections_00.append(SelectionType(ISTN.BACKGROUND, BK_appearance, 1))
data['imagetab.sparks'] = selections_00

selections_000 = []
SPARK_DETECT_ROI_appearance = SelectionAppearance()
SPARK_DETECT_ROI_appearance.set_line_params('green', 4)
SPARK_DETECT_ROI_appearance.set_active_line_params()
SPARK_DETECT_ROI_appearance.add_state_color('saved', 'orange')
selections_000.append(SelectionType(ISTN.ROI, SPARK_DETECT_ROI_appearance, -1))
data['imagetab.sparkdetect'] = selections_000

selections_001 = []
PSEUDO_LINESCAN_LINE_appearance = SelectionAppearance()
PSEUDO_LINESCAN_LINE_appearance.set_line_params('lime', 4)
PSEUDO_LINESCAN_LINE_appearance.set_active_line_params()
PSEUDO_LINESCAN_LINE_appearance.add_state_color('saved', 'orange')
selections_001.append(SelectionType(
    ISTN.LINE, PSEUDO_LINESCAN_LINE_appearance, 1))
data['imagetab.pseudolinescan'] = selections_001

selections_002 = []
ROI_appearance = SelectionAppearance()
ROI_appearance.set_line_params('green', 4)
ROI_appearance.set_active_line_params()

F0_appearance = SelectionAppearance()
F0_appearance.set_line_params('blue', 4)
F0_appearance.set_active_line_params()

selections_002.append(SelectionType(ISTN.ROI, ROI_appearance, 1))
# selections_0.append(SelectionType(ISTN.BACKGROUND,BK_appearance,1))
selections_002.append(SelectionType(ISTN.F0, F0_appearance, 1))
data['imagetab.timeaverage'] = selections_002

selections_003 = []
ROI_appearance = SelectionAppearance()
ROI_appearance.set_line_params('green', 4)
ROI_appearance.set_active_line_params()

selections_003.append(SelectionType(ISTN.ROI, ROI_appearance, -1))
data['pixelbypixeltab'] = selections_003

selections_1 = []
MANUAL_appearance = SelectionAppearance()
MANUAL_appearance.set_line_params('black', 1.5)
MANUAL_appearance.set_active_line_params('red')
MANUAL_appearance.set_fill_params('green', is_gradient=True)
MANUAL_appearance.set_active_fill_params('orange')

AUTO_appearance = SelectionAppearance()
AUTO_appearance.set_line_params('black', 1.5)
AUTO_appearance.set_active_line_params('red')
AUTO_appearance.set_fill_params('navy', is_gradient=True)
AUTO_appearance.set_active_fill_params('orange')

selections_1.append(SelectionType(TBSTN.MANUAL, MANUAL_appearance, -1))
selections_1.append(SelectionType(TBSTN.AUTO, AUTO_appearance, 1))
data['transienttab'] = selections_1

selections_2 = []
SPARK_appearance = SelectionAppearance()
SPARK_appearance.set_line_params(None, 1.5,)
SPARK_appearance.set_active_line_params('red')
SPARK_appearance.set_fill_params('black', is_gradient=True)
SPARK_appearance.set_active_fill_params('orange')


# selections_1 = []
selections_2.append(SelectionType(TBSTN.SPARK, SPARK_appearance, -1))
# selections_1.append(SelectionType('F0','purple',5))
data['sparktab'] = selections_2

selections_3 = []
pipe_roi_appearance = SelectionAppearance()
pipe_roi_appearance.set_line_params(None, 1.5,)
pipe_roi_appearance.set_active_line_params('red')
pipe_roi_appearance.set_fill_params('black', is_gradient=False, alpha=0.5)
pipe_roi_appearance.set_active_fill_params('black', alpha=0.3)


# selections_1 = []
selections_3.append(SelectionType(TBSTN.MANUAL, pipe_roi_appearance, 1))
data['pipes.singleboundary'] = selections_3

# selections_2 = []
# S1_appearance = SelectionAppearance()
# S1_appearance.set_line_params('black',1)
# S1_appearance.set_active_line_params('red')
# S1_appearance.set_fill_params('green',is_gradient=True)
# S1_appearance.set_active_fill_params('orange')
#
# S2_appearance = SelectionAppearance()
# S2_appearance.set_line_params('black',1)
# S2_appearance.set_active_line_params('red')
# S2_appearance.set_fill_params('tomato',is_gradient=True)
# S2_appearance.set_active_fill_params('orange')

# selections_2.append(SelectionType('S1',S1_appearance,1))
# selections_2.append(SelectionType('S2',S2_appearance,1))
# selections_1.append(SelectionType('F0','purple',5))
# data['transienttab.groups'] = selections_2
