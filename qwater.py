#!/usr/bin/env python3

from decimal import Decimal
from pathlib import Path
import sys

from PyQt5.QtCore import pyqtSlot as Slot, Qt
from PyQt5.QtGui import (
    QImage, QPixmap, QFont, QPen, QColor, QPainter,
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileDialog, QColorDialog, QFontDialog,
    QLabel,
)
from PyQt5.uic import loadUiType


WinUi = loadUiType(str(Path(__file__).with_name("mainwindow.ui")))[0]


class Window(QMainWindow, WinUi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.textEdit.textChanged.connect(self.paintText)
        self.textAngle.valueChanged.connect(self.paintText)
        self.textOpacity.valueChanged.connect(self.paintText)
        self.fontSize.valueChanged.connect(self.paintText)

        self.color = QColor(0, 0, 0)
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

        path, filter = QFileDialog.getSaveFileName(
            self, "Save image", str(self.lastPath),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not path:
            return

        path = Path(path)
        self.lastPath = path.parent

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

    @Slot()
    def on_actionOpen_triggered(self):
        path, filter = QFileDialog.getOpenFileName(
            self, "Open image", str(self.lastPath),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not path:
            return

        self.lastPath = Path(path).parent

        self.loadImage(path)

    def loadImage(self, path):
        self.images.append(QImage(path))

        layout = self.imagesContainer.layout()
        layout.addWidget(QLabel(parent=self.imagesContainer))
        self.paintTextImage(layout.count() - 1)

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
        painter.setFont(self.font)

        self.color.setAlpha(self.textOpacity.value())
        painter.setPen(QPen(self.color))

        text = self.textEdit.toPlainText()

        box = device.rect()
        painter.translate(box.center())
        painter.rotate(self.textAngle.value())
        painter.translate(-box.center())
        painter.drawText(box, Qt.AlignCenter, text)

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


if __name__ == "__main__":
    if sys.excepthook is sys.__excepthook__:
        sys.excepthook = lambda *args: sys.__excepthook__(*args)

    app = QApplication(sys.argv)
    win = Window()
    win.show()

    for file in app.arguments()[1:]:
        win.loadImage(file)

    app.exec()
