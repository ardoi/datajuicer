from PyQt5 import QtCore as QC
from PyQt5 import QtWidgets as QW
from PyQt5 import QtGui as QG
from snaproi import SnapROIItem
from lsjuicer.util.current import current

class MeasureROIItem(SnapROIItem):
    def __init__(self, *args, **kwargs):
        super(MeasureROIItem, self).__init__(*args, **kwargs)
        self.info_box = None
        self.info_text = None
        self.fm = None

    def mouseMoveEvent(self,event):
        SnapROIItem.mouseMoveEvent(self, event)

        #draw info box
        r = self.rect()
        scene_r = self.scene().sceneRect()
        loc = r.bottomRight()
        #add some space between line and box
        view = self.scene().views()[0]
        pad_rec = view.mapToScene(QC.QRect(0, 0, 10, 10)).boundingRect()
        loc += QC.QPoint(pad_rec.width(), pad_rec.height())
        #calculate size of info box on scene based on font size
        if self.fm:
            line_height = self.fm.lineSpacing()
        else:
            line_height = 20
        lines = 3
        extra_padding = 0.5
        multiplier = lines + extra_padding
        rec = view.mapToScene(QC.QRect(0, 0, 350, multiplier * line_height)).boundingRect()
        #make sure info box does not go out of the scene
        if loc.x() + rec.width() > scene_r.right():
            over = loc.x() + rec.width() - scene_r.right()
            loc.setX(loc.x() - over)
        if loc.y() + rec.height() > scene_r.bottom():
            over = loc.y() + rec.height() - scene_r.bottom()
            loc.setY(loc.y() - over)

        info_box_rect = QC.QRectF(loc, QC.QSizeF(rec.width(), rec.height()))

        if not self.info_box:
            self.info_box = QW.QGraphicsRectItem(self)
            color = QG.QColor('white')
            color.setAlphaF(0.7)
            self.info_box.setBrush(QG.QBrush(color))
            pen = QG.QPen(QG.QColor('black'))
            pen.setCosmetic(True)
            self.info_box.setPen(pen)
        self.info_box.setRect(info_box_rect)

        if not self.info_text:
            self.info_text = QW.QGraphicsTextItem(self)
            self.info_text.setDefaultTextColor(QG.QColor('black'))
            self.info_text.setFlag(QW.QGraphicsItem.ItemIgnoresTransformations)
            #self.info_text.setPos(QC.QPointF(0,0))
            font = self.info_text.font()
            font.setFamily('Courier')
            font.setStyleHint(QG.QFont.TypeWriter)
            font.setBold(True)
            font.setPointSize(15)
            self.fm = QG.QFontMetrics(font)
            self.info_text.setFont(font)
        self.info_text.setPos(loc)
        format_string = """<p>
        min:{:.4g}, max:{:.4g}<br>
        mean:{:.4g}, pixels:{:d}<br>
        &Delta;x:{:.4g}, &Delta;y:{:.4g}<br></p>
        """
        p1 = r.topLeft()
        p2 = r.bottomRight()
        dd = current.displayed[p1.y():p2.y(), p1.x():p2.x()]
        info_string = format_string.format(dd.min(),dd.max(),
                                            dd.mean(),dd.size,
                                            p2.x() - p1.x(),
                                            p2.y() - p1.y())
        self.info_text.setHtml(info_string)

