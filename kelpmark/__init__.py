#!/usr/bin/env python3
# SPDX-License-Identifier: Unlicense

from decimal import Decimal
from pathlib import Path
import sys

from popplerqt5 import Poppler
from PyQt5.QtCore import pyqtSlot as Slot, Qt
from PyQt5.QtGui import (
    QImage, QPixmap, QFont, QPen, QColor, QPainter,
    QPageSize, QTransform, QFontMetricsF,
)
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileDialog, QColorDialog, QFontDialog, QInputDialog,
    QLabel, QGraphicsColorizeEffect,
)
from PyQt5.uic import loadUiType


__version__ = "1.0.0"


WinUi = loadUiType(str(Path(__file__).with_name("mainwindow.ui")))[0]

RENDER_HINTS = (
    Poppler.Document.RenderHint.Antialiasing
    | Poppler.Document.RenderHint.TextAntialiasing
)


class ResolutionDialog(QInputDialog):
    def __init__(self, pageSize, *args, **kwargs):
        file = kwargs.pop("file", None)

        super().__init__(*args, **kwargs)
        self.pageSize = pageSize

        title = self.tr("PDF importing resolution")
        if file:
            title = self.tr("{} importing resolution").format(Path(file).name)

        self.setWindowTitle(title)
        self.setInputMode(QInputDialog.IntInput)
        self.setIntRange(10, 600)
        self.intValueChanged.connect(self.updateLabel)

        self.setIntValue(72)

    @Slot(int)
    def updateLabel(self, dpi):
        dpi = Decimal(dpi)
        newSize = self.pageSize * dpi / 72
        self.setLabelText(f"DPI (computed dimensions: {newSize.width()}x{newSize.height()} px)")


class Window(QMainWindow, WinUi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.textEdit.textChanged.connect(self.paintText)
        self.textAngle.valueChanged.connect(self.paintText)
        self.textOpacity.valueChanged.connect(self.paintText)
        self.fontSize.valueChanged.connect(self.paintText)
        self.tilingBox.toggled.connect(self.paintText)
        self.staggeredBox.toggled.connect(self.paintText)
        self.boldBox.toggled.connect(self.paintText)
        self.widthSpacing.valueChanged.connect(self.paintText)
        self.heightSpacing.valueChanged.connect(self.paintText)

        self.color = QColor(0, 0, 0)
        effect = QGraphicsColorizeEffect()
        effect.setColor(self.color)
        self.colorButton.setGraphicsEffect(effect)

        self.font = QFont("Serif", 32)
        self.fontButton.setText(self.font.family())

        self.images = []
        self.lastPath = Path.cwd()
        self.zoom = Decimal(1)

    @Slot()
    def on_colorButton_clicked(self):
        new = QColorDialog.getColor(self.color, self)
        if not new.isValid():
            return

        self.color = new

        effect = QGraphicsColorizeEffect()
        effect.setColor(self.color)
        self.colorButton.setGraphicsEffect(effect)

        self.paintText()

    @Slot()
    def on_fontButton_clicked(self):
        font, valid = QFontDialog.getFont(self.font, self)
        if not valid:
            return

        self.font = font
        self.fontButton.setText(self.font.family())
        self.fontSize.setValue(self.font.pointSize())
        self.paintText()

    @Slot()
    def on_actionSave_triggered(self):
        if not self.images:
            return

        path, filter_ = QFileDialog.getSaveFileName(
            self, self.tr("Save image"), str(self.lastPath),
            self.tr("Images (*.jpg *.jpeg *.png);;PDF (*.pdf)"),
        )
        if not path:
            return

        if path.rpartition(".")[2] not in {"png", "jpg", "jpeg", "pdf"}:
            if "pdf" in filter_:
                path += ".pdf"
            else:
                path += ".jpg"

        path = Path(path)
        self.lastPath = path.parent

        if path.suffix == ".pdf":
            self.saveAsPdf(path)
        else:
            self.saveAsImages(path)

    def saveAsImages(self, path):
        if len(self.images) == 1:
            target = self.images[0].copy()
            self.paintOn(target)
            target.save(str(path))
        else:
            path = Path(path)
            for n, source in enumerate(self.images, 1):
                target = source.copy()
                self.paintOn(target)
                target.save(f"{path.parent}/{path.stem}-{n:02d}{path.suffix}")

    def saveAsPdf(self, path):
        pdf = QPrinter()
        pdf.setFullPage(True)
        pdf.setOutputFileName(str(path))

        first = True
        painter = QPainter()

        for source in self.images:
            marked = source.copy()
            self.paintOn(marked)

            pdf.setPageSize(QPageSize(marked.size()))

            if first:
                first = False
                painter.begin(pdf)
            else:
                pdf.newPage()

            # though we set page size, the rect is not the same
            rect = marked.rect()
            rect.setWidth(pdf.width())
            rect.setHeight(pdf.height())
            painter.drawImage(rect, marked)

        painter.end()

    @Slot()
    def on_actionOpen_triggered(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open image"), str(self.lastPath),
            self.tr("Images/PDF (*.png *.jpg *.jpeg *.pdf)"),
        )
        if not path:
            return

        self.lastPath = Path(path).parent

        self.loadFile(path)

    def loadFile(self, path):
        if path.endswith(".pdf"):
            self.loadPdf(path)
        else:
            self.loadImage(path)

    def loadImage(self, path):
        self.addImage(QImage(path))

    def addImage(self, image):
        self.images.append(image)

        layout = self.imagesContainer.layout()
        layout.addWidget(QLabel(parent=self.imagesContainer))
        self.paintTextImage(layout.count() - 1)

    def loadPdf(self, path):
        doc = Poppler.Document.load(path)
        page = doc.page(0)
        dlg = ResolutionDialog(page.pageSize(), file=path, parent=self)
        dlg.exec()
        res = dlg.intValue()

        doc.setRenderHint(RENDER_HINTS)
        for i in range(doc.numPages()):
            page = doc.page(i)
            image = page.renderToImage(res, res)
            self.addImage(image)

    def getImageWidget(self, i):
        return self.imagesContainer.layout().itemAt(i).widget()

    @Slot()
    def paintText(self):
        for i in range(self.imagesContainer.layout().count()):
            self.paintTextImage(i)

    def paintTextImage(self, i):
        if not self.images:
            return

        source = self.images[i]

        target = source.copy()
        self.paintOn(target)
        target = target.scaled(
            target.size() * self.zoom,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.getImageWidget(i).setPixmap(QPixmap(target))

    def paintOn(self, device):
        painter = QPainter(device)

        self.font.setPointSize(self.fontSize.value())
        self.font.setBold(self.boldBox.isChecked())
        painter.setFont(self.font)

        self.color.setAlpha(self.textOpacity.value())
        painter.setPen(QPen(self.color))

        text = self.textEdit.toPlainText()

        box = painter.boundingRect(device.rect(), Qt.AlignCenter, text)

        transform = QTransform()
        center = box.center()
        transform.translate(center.x(), center.y())
        transform.rotate(self.textAngle.value())
        transform.translate(-center.x(), -center.y())

        def paintWith(tileform):
            combined = tileform * transform
            if not combined.mapRect(box).intersects(device.rect()):
                return False

            painter.setTransform(combined)
            painter.drawText(box, Qt.AlignCenter, text)
            return True

        def paintTile(x, y):
            tile = QTransform()

            stagger = 0
            if y % 2 and self.staggeredBox.isChecked():
                stagger = 0.5

            tile.translate(
                (stagger + x) * (box.width() + metrics.horizontalAdvance(" ") * self.widthSpacing.value() / 100),
                y * (box.height() + metrics.lineSpacing() * self.heightSpacing.value() / 100),
            )
            return paintWith(tile)

        # paint on center
        paintWith(QTransform())

        if self.tilingBox.isChecked():
            # paint tiles with increasing distance
            # xxxxx
            # x...x
            # x.o.x
            # x...x
            # xxxxx

            metrics = QFontMetricsF(self.font)

            for radius in range(1, 1000):
                has_painted = False

                for x in range(-radius, radius + 1):
                    has_painted = paintTile(x, -radius) or has_painted
                    has_painted = paintTile(x, radius) or has_painted
                for y in range(-radius + 1, radius):
                    has_painted = paintTile(-radius, y) or has_painted
                    has_painted = paintTile(radius, y) or has_painted

                if not has_painted:
                    # everything was out of bounds, so will the next radius
                    break

        painter.end()

    @Slot()
    def on_actionZoomOriginal_triggered(self):
        self.zoom = Decimal("1")
        self.paintText()

    @Slot()
    def on_actionZoomIn_triggered(self):
        self.zoom *= Decimal("1.5")
        self.paintText()

    @Slot()
    def on_actionZoomOut_triggered(self):
        self.zoom /= Decimal("1.5")
        self.paintText()


def main():
    if sys.excepthook is sys.__excepthook__:
        sys.excepthook = lambda *args: sys.__excepthook__(*args)

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    for file in app.arguments()[1:]:
        win.loadFile(file)

    app.exec()


if __name__ == "__main__":
    main()
