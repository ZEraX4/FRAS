import sys
import time

import cv2
import numpy as np
import imagezmq
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QPixmap, QImage
from PyQt5.QtWidgets import QDialog, QApplication, QGraphicsScene
from qimage2ndarray import array2qimage

from utils import debug


class Thread(QThread):
    """
    Thread used for sending frames to the server
    """
    change = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()

        self.sendHub = imagezmq.ImageSender(connect_to='tcp://127.0.0.1:5555')

    def run(self):
        """
        Main routine
        :return: Nothing
        """
        debug(1, "Starting Thread...")
        cap = cv2.VideoCapture(0)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        font = cv2.FONT_HERSHEY_DUPLEX

        while True:
            found = False
            grabbed, frame = cap.read()
            if not grabbed:
                break

            rep = self.sendHub.send_image("Node1", frame)

            if rep is None:
                continue
            rep = str(rep).split("'")[1]

            try:
                int(rep)
                frame = np.zeros_like(frame)
                cv2.putText(frame, f"{rep}", (h//4, int(w//2.37)), font, 5, (0, 255, 0), 5)
                found = True
            except ValueError:
                cv2.putText(frame, f"{rep}", (6, 150), font, 1, (0, 0, 255), 2)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = array2qimage(frame)
            self.change.emit(frame)
            if found:
                time.sleep(1)


class Ui_View(QDialog):
    """
    Main view
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setObjectName("View")
        self.setWindowModality(QtCore.Qt.NonModal)
        self.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.cameraView = QtWidgets.QGraphicsView(self)
        self.cameraView.setObjectName("cameraView")
        self.gridLayout.addWidget(self.cameraView, 0, 0, 1, 1)

        self.scene = QGraphicsScene(self.cameraView)
        self.thread = Thread()

        self.thread.change.connect(self.change)

        self.thread.start()

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        """
        Translate strings
        :return:
        """
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("View", "View"))

    def change(self, frame):
        """
        Change the frame of the view
        :param frame: np.array() - Frame
        :return: Nothing
        """
        pix = QPixmap.fromImage(frame.scaled(self.cameraView.size() - QtCore.QSize(2, 2)))
        self.scene.clear()
        self.scene.addPixmap(pix)
        self.cameraView.setScene(self.scene)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    form = Ui_View()
    form.setWindowFlags(form.windowFlags() | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowMinMaxButtonsHint)
    form.setWindowTitle("FRAS - Node")
    app.setWindowIcon(QtGui.QIcon('icon.png'))

    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    form.show()
    sys.exit(app.exec_())
