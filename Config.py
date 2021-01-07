import pickle
import sys

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QPalette, QColor, QRegExpValidator
from PyQt5.QtWidgets import QDialog, QApplication

from utils import debug

koskos = {}
ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
portValid = QRegExpValidator(QRegExp("[0-5][0-9][0-9][0-9][0-9]|"
                                     "6[0-4][0-9][0-9][0-9]|"
                                     "65[0-4][0-9][0-9]|"
                                     "655[0-2][0-9]|"
                                     "6553[0-5]"))
ipRegex = QRegExp("^" + ipRange +
                  "\\." + ipRange +
                  "\\." + ipRange +
                  "\\." + ipRange + "$")
ipValid = QRegExpValidator(ipRegex)


class Ui_Config(QDialog):
    def __init__(self):
        super().__init__()
        self.setObjectName("self")
        self.resize(345, 75)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.addNode = QtWidgets.QPushButton(self)
        self.addNode.setObjectName("addNode")
        self.horizontalLayout.addWidget(self.addNode)
        self.addCam = QtWidgets.QPushButton(self)
        self.addCam.setObjectName("addCam")
        self.horizontalLayout.addWidget(self.addCam)
        self.save = QtWidgets.QPushButton(self)
        self.save.setObjectName("save")
        self.horizontalLayout.addWidget(self.save)
        self.verticalLayout.addLayout(self.horizontalLayout)

        def addcam():
            self.add_camera()

        def addnode():
            self.add_node()

        self.load_file()

        self.addCam.clicked.connect(addcam)
        self.addNode.clicked.connect(addnode)
        self.save.clicked.connect(self.save_file)
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Config"))
        self.addNode.setText(_translate("self", "Add Node"))
        self.addCam.setText(_translate("self", "Add Camera"))
        self.save.setText(_translate("self", "Save"))

    def add_camera(self, name="", loc="", ard=""):
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.setObjectName("camera")
        camName = QtWidgets.QLineEdit()
        camName.setObjectName("camName")
        camName.setText(name)
        camName.setPlaceholderText("Camera Name")
        horizontalLayout.addWidget(camName)
        camLocation = QtWidgets.QLineEdit()
        camLocation.setObjectName("camLocation")
        camLocation.setValidator(ipValid)
        camLocation.setText(loc)
        camLocation.setPlaceholderText("Came IP/Number")
        horizontalLayout.addWidget(camLocation)
        arduinoLocation = QtWidgets.QLineEdit()
        arduinoLocation.setObjectName("arduinoLocation")
        arduinoLocation.setValidator(ipValid)
        arduinoLocation.setText(ard)
        arduinoLocation.setPlaceholderText("Arduino IP")
        horizontalLayout.addWidget(arduinoLocation)
        deleteItem = QtWidgets.QPushButton()
        p = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(149, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        deleteItem.setPalette(p)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Icons/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        deleteItem.setIcon(icon)
        # deleteItem.setFlat(True)
        deleteItem.setObjectName("deleteItem")
        deleteItem.setObjectName("deleteItem")

        horizontalLayout.addWidget(deleteItem)
        deleteItem.clicked.connect(lambda: self.delete_item(horizontalLayout))
        self.verticalLayout.addLayout(horizontalLayout)

    def add_node(self, name="", loc=""):
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.setObjectName("node")
        nodeName = QtWidgets.QLineEdit()
        nodeName.setObjectName("nodeName")
        nodeName.setPlaceholderText("Node ID")
        nodeName.setText(name)
        horizontalLayout.addWidget(nodeName)
        nodeLocation = QtWidgets.QLineEdit()
        nodeLocation.setObjectName("nodeLocation")
        nodeLocation.setValidator(portValid)
        nodeLocation.setPlaceholderText("Node Port")
        nodeLocation.setText(loc)
        horizontalLayout.addWidget(nodeLocation)
        deleteItem = QtWidgets.QPushButton()
        p = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(149, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        p.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        deleteItem.setPalette(p)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Icons/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        deleteItem.setIcon(icon)
        # deleteItem.setFlat(True)
        deleteItem.setObjectName("deleteItem")

        horizontalLayout.addWidget(deleteItem)
        deleteItem.clicked.connect(lambda: self.delete_item(horizontalLayout))
        self.verticalLayout.addLayout(horizontalLayout)

    def delete_item(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        layout.setParent(None)

        if self.verticalLayout.count() < 2:
            self.add_node()
        self.resize(345, 0)

    def load_file(self):
        global koskos
        try:
            with open('data.dat', 'rb') as f:
                koskos = pickle.load(f)
            if len(koskos.keys()) < 1:
                self.add_node()
            for k in koskos.keys():
                v = koskos[k]
                if len(v) == 2:
                    self.add_camera(k, v[0], v[1])
                else:
                    self.add_node(k, v)
        except (FileNotFoundError, EOFError):
            debug(2, "data.dat is not existed, will be created after you save.")
            self.add_camera()

    def save_file(self):
        koskos = {}
        for layout in self.verticalLayout.children():
            if type(layout) is QtWidgets.QHBoxLayout:
                data = list()
                if layout.objectName() != "horizontalLayout":
                    for i in range(layout.count()):
                        item = layout.itemAt(i).widget()
                        if type(item) is QtWidgets.QLineEdit:
                            if item.text() == "" and item.objectName() != "arduinoLocation":
                                debug(2, "One of the inputs is empty, arduino input is optional.")
                                return
                            data.append(item.text())
                if layout.objectName() == "camera":
                    koskos[data[0]] = (data[1], data[2])
                elif layout.objectName() == "node":
                    koskos[data[0]] = data[1]
        with open('data.dat', 'wb') as f:
            pickle.dump(koskos, f)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    form = Ui_Config()
    form.setWindowFlags(form.windowFlags() |
                        QtCore.Qt.WindowSystemMenuHint |
                        QtCore.Qt.WindowMinMaxButtonsHint)
    form.setWindowTitle("Face Recognition - Config")
    app.setWindowIcon(QtGui.QIcon('Icons/icon.png'))
    # app.setStyleSheet(qdarkstyle.load_stylesheet())

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
