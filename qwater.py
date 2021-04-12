#!/usr/bin/env python3

import os
import sys

from PyQt5.QtCore import pyqtSlot as Slot
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

        self.color = QColor(0, 0, 0)
        self.font = QFont("Serif", 32)
        self.fontButton.setText(self.font.family())

        self.image = None

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
        self.paintText()

    @Slot()
    def on_actionOpen_triggered(self):
        path = QFileDialog.getOpenFileName(
            self, "Open image", os.getcwd(),
            "Images (*.png *.jpg *.jpeg)",
        )
        if not path[0]:
            return
        self.loadImage(path[0])

    def loadImage(self, path):
        self.image = QImage(path)
        self.paintText()

    @Slot()
    def paintText(self):
        if not self.image:
            return

        target = self.image.copy()
        self.paintOn(target)
        self.imgDisplay.setPixmap(QPixmap(target))

    def paintOn(self, device):
        painter = QPainter(device)

        # self.font.setPointSize(self.fontSize.value())
        painter.setFont(self.font)

        self.color.setAlpha(self.textOpacity.value())
        painter.setPen(QPen(self.color))

        text = self.textEdit.toPlainText()

        painter.drawText(5, 50, text)

        painter.end()


if __name__ == "__main__":
    if sys.excepthook is sys.__excepthook__:
        sys.excepthook = lambda *args: sys.__excepthook__(*args)

    app = QApplication([])
    win = Window()
    win.show()
    app.exec()
