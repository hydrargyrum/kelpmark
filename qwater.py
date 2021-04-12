#!/usr/bin/env python3

from decimal import Decimal
import os
from pathlib import Path
import sys

from PyQt5.QtCore import pyqtSlot as Slot, Qt
from PyQt5.QtGui import (
    QImage, QPixmap, QFont, QPen, QColor, QPainter,
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileDialog, QColorDialog, QFontDialog,
)
from PyQt5.uic import loadUiType


WinUi = loadUiType(str("mainwindow.ui"))[0]


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

        self.image = None
        self.path = Path.cwd() / "fake"
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
        if not self.image:
            return

        path = QFileDialog.getSaveFileName(
            self, "Save image", str(self.path.parent),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not path[0]:
            return

        self.path = Path(path[0])
        target = self.image.copy()
        self.paintOn(target)
        target.save(str(self.path))

    @Slot()
    def on_actionOpen_triggered(self):
        path = QFileDialog.getOpenFileName(
            self, "Open image", str(self.path.parent),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not path[0]:
            return
        self.path = Path(path[0])
        self.loadImage(str(self.path))

    def loadImage(self, path):
        self.image = QImage(path)
        self.paintText()

    @Slot()
    def paintText(self):
        if not self.image:
            return

        target = self.image.copy()
        self.paintOn(target)
        target = target.scaled(
            target.size() * self.zoom,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.imgDisplay.setPixmap(QPixmap(target))

    def paintOn(self, device):
        painter = QPainter(device)

        self.font.setPointSize(self.fontSize.value())
        painter.setFont(self.font)

        self.color.setAlpha(self.textOpacity.value())
        painter.setPen(QPen(self.color))

        text = self.textEdit.toPlainText()

        painter.drawText(device.rect(), Qt.AlignCenter, text)

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

    app = QApplication([])
    win = Window()
    win.show()
    app.exec()
