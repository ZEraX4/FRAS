import multiprocessing
import os
import pickle
import sys
import time
from distutils.util import strtobool

import cv2
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QMetaObject, QSize, Qt, QDateTime, QSettings, QSortFilterProxyModel
from PyQt5.QtGui import QPixmap, QFont, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QGraphicsScene, QPushButton, QHBoxLayout, QProgressBar, QDialog, \
    QFrame, QAbstractScrollArea, QTableView, QLabel, QVBoxLayout, QGroupBox, QGraphicsView, QGridLayout, \
    QAbstractItemView, QCheckBox, QDateTimeEdit, QSpinBox, QDoubleSpinBox, QToolButton, QLineEdit, QFileDialog, \
    QMessageBox, QComboBox

from Config import Ui_Config
from Processor import Processor
from Thread import Thread
from utils import file_save, debug, DEBUG

# Encoding file path
encFile = 'enc.dat'
# Temp file used for processType algorithm
tempFile = 'tmp.dat'
# Path to where to save the logs
LOGDIR = 'log'
# Name of the key in the registry
SETTINGS = "test"
# Data variables
ids = list()
encodings = list()
# The temp variable used for processType algorithm
temp = {}
# Lists of the hours used for determining the type of attendance
timeIn = sorted([a for i in range(4) for a in (i, i + 8, i + 16)])
timeOut = sorted([a for i in range(4) for a in (i + 4, i + 12, i + 20)])


# noinspection PyUnresolvedReferences,PyTypeChecker
class MainDialog(QDialog):
    def __init__(self, parent=None):
        """
        The main dialog of the program
        :param parent: Parent of the dialog
        """
        super(MainDialog, self).__init__(parent)

        def changeFilter(ind):
            self.filter_proxy_model.setFilterKeyColumn(ind - 1)

        def clearLog():
            self.model.removeRows(0, self.model.rowCount())

        def loadLog():
            try:
                with open('log.txt', 'r') as f:
                    for line in f.readlines():
                        data = line.split('\t')
                        date = data[1] + ' - ' + data[2]
                        self.addItem(data[0], data[3].strip(), date=date)
            except FileNotFoundError:
                QMessageBox.warning(None, "Error", "No log file found.", QMessageBox.Ok)

        def startConfig():
            cfg = Ui_Config()
            cfg.exec_()
            self.readKoskos()
            self.setupCams()

        def clear():
            self.settings.beginGroup(SETTINGS)
            if self.sender().objectName() == "save_action":
                self.savePath.setText("")
                self.settings.setValue("Save_Path", "")
            elif self.sender().objectName() == "enc_action":
                self.encPath.setText("")
                self.settings.setValue("Encodings_Path", "")
            self.settings.endGroup()

        def slot_check():
            self.check_path(self.sender().text())

        self.settings = QSettings("ZEraX", "FRAS")
        self.settings.beginGroup(SETTINGS)

        self.koskos = None
        self.readKoskos()
        self.cameras = list()
        self.threads = list()
        self.processes = list()
        self.row, self.col = 0, 0
        self.shared = multiprocessing.Value('b', True)

        if self.objectName():
            self.setObjectName(u"Dialog")
        # self.resize(775, 450)
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setObjectName(u"gridLayout")
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setObjectName(u"mainLayout")
        self.frameGB = QGroupBox(self)
        self.frameGB.setObjectName(u"frameGB")
        self.camLayout = QGridLayout(self.frameGB)
        self.camLayout.setObjectName(u"camLayout")

        self.mainLayout.addWidget(self.frameGB)

        self.toolsGB = QGroupBox(self)
        self.toolsGB.setObjectName(u"toolsGB")
        self.toolsGB.setMaximumSize(QtCore.QSize(300, 16777215))
        self.verticalLayout = QVBoxLayout(self.toolsGB)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.outLabel = QLabel(self.toolsGB)
        self.outLabel.setObjectName(u"outLabel")
        self.outLabel.setEnabled(True)
        self.outLabel.setMinimumSize(QSize(200, 65))
        font = QFont()
        font.setFamily(u"Arial Bold")
        font.setPointSize(36)
        font.setBold(True)
        font.setWeight(75)
        self.outLabel.setFont(font)
        self.outLabel.setFrameShape(QFrame.StyledPanel)
        self.outLabel.setLineWidth(1)
        self.outLabel.setScaledContents(True)
        self.outLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.outLabel)

        self.saveLayout = QHBoxLayout()
        self.saveLayout.setContentsMargins(0, 0, 0, 0)
        self.saveLayout.setObjectName("saveLayout")
        self.savePath = QLineEdit(self.toolsGB)
        self.savePath.setObjectName("savePath")
        self.savePath.setPlaceholderText("Log Folder Path")
        self.savePath.setToolTip("Path to where you want to save the logs.")
        path = self.settings.value("Save_Path")
        self.savePath.setText(path if path is not None else "")
        self.saveLayout.addWidget(self.savePath)
        self.getSPath = QToolButton(self.toolsGB)
        self.getSPath.setObjectName("getSPath")
        self.getSPath.setText("...")
        self.saveLayout.addWidget(self.getSPath)
        action = self.savePath.addAction(QIcon("Icons/delete.png"), QLineEdit.TrailingPosition)
        action.setObjectName("save_action")
        action.triggered.connect(clear)

        self.verticalLayout.addLayout(self.saveLayout)

        self.encLayout = QHBoxLayout()
        self.encLayout.setContentsMargins(0, 0, 0, 0)
        self.encLayout.setObjectName("encLayout")
        self.encPath = QLineEdit(self.toolsGB)
        self.encPath.setObjectName("encPath")
        self.encPath.setPlaceholderText("Encoding Folder Path")
        self.encPath.setToolTip("Used for checking if the logged image match the encoded one.")
        path = self.settings.value("Encodings_Path")
        self.encPath.setText(path if path is not None else "")
        self.encLayout.addWidget(self.encPath)
        self.getPath = QToolButton(self.toolsGB)
        self.getPath.setObjectName("getPath")
        self.getPath.setText("...")
        self.encLayout.addWidget(self.getPath)
        action = self.encPath.addAction(QIcon("Icons/delete.png"), QLineEdit.TrailingPosition)
        action.setObjectName("enc_action")
        action.triggered.connect(clear)

        self.verticalLayout.addLayout(self.encLayout)

        filterLayout = QHBoxLayout()
        lineEdit = QLineEdit(self.toolsGB)
        lineEdit.setPlaceholderText("Filter...")
        filterList = QComboBox(self.toolsGB)
        filterList.addItems(['ALL', 'ID', 'TYPE', 'DATE', 'DIST'])
        filterLayout.addWidget(lineEdit)
        filterLayout.addWidget(filterList)

        self.verticalLayout.addLayout(filterLayout)

        # standard item model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['ID', 'TYPE', 'DATE', 'DIST'])

        # filter proxy model
        self.filter_proxy_model = QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterKeyColumn(-1)

        self.attendanceTable = QTableView(self.toolsGB)
        self.attendanceTable.setModel(self.filter_proxy_model)
        self.attendanceTable.setColumnWidth(0, 36)
        self.attendanceTable.setColumnWidth(1, 30)
        self.attendanceTable.setColumnWidth(2, 120)
        self.attendanceTable.setColumnWidth(3, 30)
        self.attendanceTable.horizontalHeader().setStretchLastSection(True)
        self.attendanceTable.setObjectName(u"attendanceTable")
        self.attendanceTable.setToolTip("Click at any cell to open the logged image, and the encoded image if the "
                                        "Encodings path is set")
        self.attendanceTable.setFrameShape(QFrame.StyledPanel)
        self.attendanceTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.attendanceTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.verticalLayout.addWidget(self.attendanceTable)

        self.progressLayout = QHBoxLayout()
        self.toleranceWidget = QDoubleSpinBox(self.toolsGB)
        self.toleranceWidget.setMaximum(1.0)
        self.toleranceWidget.setSingleStep(0.01)
        val = self.settings.value("Tolerance")
        self.toleranceWidget.setProperty("value", val if val is not None else 0.5)
        self.toleranceWidget.setObjectName("toleranceWidget")
        self.toleranceWidget.setToolTip("Tolerance, Max = 1")
        self.progressLayout.addWidget(self.toleranceWidget)
        self.tolerance = multiprocessing.Value('d', self.toleranceWidget.value())

        self.progressBar = QProgressBar(self.toolsGB)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressLayout.addWidget(self.progressBar)

        self.config = QPushButton(self.toolsGB)
        self.config.setObjectName("config")
        self.progressLayout.addWidget(self.config)
        self.verticalLayout.addLayout(self.progressLayout)

        self.registerLayout = QHBoxLayout()
        self.registerLayout.setObjectName(u"registerLayout")
        self.startBtn = QPushButton(self.toolsGB)
        self.startBtn.setObjectName(u"startBtn")

        self.registerLayout.addWidget(self.startBtn)

        self.clearLog = QPushButton(self.toolsGB)
        self.setObjectName(u"clearLog")
        self.loadLog = QPushButton(self.toolsGB)
        self.loadLog.setObjectName(u"loadLog")
        self.registerLayout.addWidget(self.clearLog)
        self.registerLayout.addWidget(self.loadLog)

        self.stopBtn = QPushButton(self.toolsGB)
        self.stopBtn.setObjectName(u"stopBtn")
        self.stopBtn.setEnabled(False)

        self.registerLayout.addWidget(self.stopBtn)

        self.verticalLayout.addLayout(self.registerLayout)

        self.mainLayout.addWidget(self.toolsGB)

        self.gridLayout.addLayout(self.mainLayout, 0, 0, 1, 1)

        self.settings.endGroup()

        self.setupCams()

        self.retranslateUi(self)
        self.getPath.clicked.connect(self.get_folder)
        self.encPath.editingFinished.connect(slot_check)
        self.getSPath.clicked.connect(self.get_folder)
        self.savePath.editingFinished.connect(slot_check)
        self.config.clicked.connect(startConfig)
        self.startBtn.clicked.connect(self.startCamera)
        self.stopBtn.clicked.connect(self.stop)
        self.attendanceTable.doubleClicked.connect(self.get_image)
        self.clearLog.clicked.connect(clearLog)
        self.loadLog.clicked.connect(loadLog)
        lineEdit.textChanged.connect(self.filter_proxy_model.setFilterRegExp)
        filterList.currentIndexChanged.connect(changeFilter)
        self.toleranceWidget.valueChanged.connect(self.setTolerance)
        QMetaObject.connectSlotsByName(self)
        # setupUi

    def retranslateUi(self, Dialog):
        """
        Translate the text of the dialog
        :param Dialog: Needed to set the title of the dialog
        :return: Nothing
        """
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", u"Dialog", None))
        self.frameGB.setTitle(_translate("Dialog", u"Frame", None))
        self.toolsGB.setTitle(_translate("Dialog", u"Tools", None))
        self.outLabel.setText(_translate("Dialog", u"Last ID", None))
        self.config.setText(_translate("Dialog", u"Config", None))
        self.startBtn.setText(_translate("Dialog", u"Start", None))
        self.clearLog.setText(_translate("Dialog", u"Clear Log", None))
        self.loadLog.setText(_translate("Dialog", u"Load Log", None))
        self.stopBtn.setText(_translate("Dialog", u"Stop", None))

        __sortingEnabled = self.attendanceTable.isSortingEnabled()
        self.attendanceTable.setSortingEnabled(False)
        self.attendanceTable.setSortingEnabled(__sortingEnabled)

    def readKoskos(self):
        """
        Read the data file
        :return: Nothing
        """
        while True:
            try:
                with open('data.dat', 'rb') as f:
                    self.koskos = pickle.load(f)
                    if len(self.koskos.items()) < 1:
                        raise ValueError
                    break
            except (SyntaxError, FileNotFoundError, EOFError, ValueError):
                r = QMessageBox.warning(None, "Error",
                                        "Config file is not setup properly,"
                                        " Do you want to set it up now?", QMessageBox.Ok | QMessageBox.Cancel)
                if r == QMessageBox.Ok:
                    c = Ui_Config()
                    c.exec_()
                    continue
                else:
                    sys.exit(0)

    def get_folder(self):
        """
        Slot used to get save folder path
        :return: Nothing
        """
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.check_path(path)

    def check_path(self, path):
        """
        Check if the provided path is writable
        :return: Nothing
        """
        if path != "" or os.path.exists(path):
            if not os.access(path, os.W_OK):
                QMessageBox.warning(None, "Error", "Path folder is not writable", QMessageBox.Ok)
                return
        else:
            return

        if self.sender().objectName() in ["getPath", "getSPath"] or \
                self.sender().sender().objectName() in ["savePath", "encPath"]:
            self.settings.beginGroup(SETTINGS)

            if self.sender().objectName() == "getSPath" or self.sender().sender().objectName() == "savePath":
                self.savePath.setText(path)
                self.settings.setValue("Save_Path", path)
            else:
                self.encPath.setText(path)
                self.settings.setValue("Encodings_Path", path)
            self.settings.endGroup()

    def setupCams(self):
        """
        Setup the cameras views and their corresponding thread and process
        :return: Nothing
        """
        for i in reversed(range(self.camLayout.count())):
            self.camLayout.itemAt(i).widget().setParent(None)
            self.processes.pop(i)
            self.threads.pop(i)
        self.row, self.col = 0, 0
        for i, k in enumerate(self.koskos.keys()):
            v = self.koskos[k]
            if len(v) == 2:
                thread, proc = self.createCamera(i, v[0], v[1], k)
            else:
                thread, proc = self.createCamera(i, "", "", k, (k, v))
            self.threads.append(thread)
            self.processes.append(proc)

    def setTolerance(self, val):
        """
        Set tolerance of the comparing function
        :param val: float - The value of the tolerance
        :return: Nothing
        """
        with self.tolerance:
            self.tolerance.get_lock()
            self.tolerance.value = val
            self.settings.beginGroup(SETTINGS)
            self.settings.setValue("Tolerance", val)
            self.settings.endGroup()

    def createCamera(self, cId, cap, ard, name="Default", node=None):
        """
        Create camera view and initiate thread and process connected to the camera
        :param node: tuple - (Node ID, Port)
        :param cId: int - Camera ID
        :param cap: str - URL of the camera
        :param ard: str - URL of the arduino
        :param name: str - Name of the view
        :return: Nothing
        """
        cameraView = QGraphicsView(self.frameGB)
        cameraView.setObjectName(u"cameraView" + str(cId))
        cameraView.setMinimumSize(QSize(400, 400))
        cameraView.setAlignment(Qt.AlignHCenter)
        self.cameras.append(cameraView)
        scene = QGraphicsScene(cameraView)
        scene.setObjectName(u"scene" + str(cId))
        label = QLabel(cameraView)
        label.setText(f"{name} ({cap if node is None else node[1]})")
        label.setAlignment(Qt.AlignCenter)
        box = QHBoxLayout(cameraView)
        box.setAlignment(Qt.AlignBottom)
        closeBtn = QPushButton(cameraView)
        closeBtn.setIcon(QIcon('Icons/play.png'))
        closeBtn.setIconSize(QSize(25, 25))
        closeBtn.setFlat(True)
        box.addStretch(0)
        box.addWidget(closeBtn)
        box.addStretch(-1)

        self.settings.beginGroup(name)
        fr = self.settings.value("fromTime")
        to = self.settings.value("toTime")
        ev = self.settings.value("every")
        re = self.settings.value("record")
        dl = self.settings.value("daily")
        self.settings.endGroup()

        checkBox = QCheckBox(cameraView)
        checkBox.setObjectName(u"record")
        checkBox.setText(u"R")
        checkBox.setToolTip("Record Schedule")
        checkBox.setChecked(strtobool(re) if re is not None else False)
        closeBtn.setEnabled(not checkBox.isChecked())
        box.addWidget(checkBox)

        daily = QCheckBox(cameraView)
        daily.setObjectName(u"daily")
        daily.setText(u"D")
        daily.setToolTip("Record daily at the same time")
        daily.setChecked(strtobool(dl) if dl is not None else False)
        box.addWidget(daily)

        every = QSpinBox(cameraView)
        every.setObjectName("every")
        every.setValue(int(ev) if ev is not None else 0)
        every.setToolTip(f"Record every {every.value()} hours from the start time")
        box.addWidget(every)

        fromEdit = QDateTimeEdit(cameraView)
        fromEdit.setObjectName(u'fromEdit')
        fromEdit.setToolTip("Starting Time")
        fromEdit.setDateTime(QDateTime.currentDateTime() if fr is None else fr)
        box.addWidget(fromEdit)
        toEdit = QDateTimeEdit(cameraView)
        toEdit.setObjectName(u'toEdit')
        toEdit.setToolTip("Finishing Time")
        toEdit.setDateTime(QDateTime.currentDateTime() if to is None else to)
        box.addWidget(toEdit)

        cameraView.setScene(scene)
        self.camLayout.addWidget(cameraView, self.row, self.col)
        if self.row == self.col:
            self.col += 1
            self.row = 0
        elif self.col - self.row == 1:
            self.row = self.col
            self.col = 0
        elif self.col < self.row:
            self.col += 1
        else:
            self.row += 1

        def send():
            thread.record(fromEdit.dateTime(), toEdit.dateTime(), every.value())
            self.settings.beginGroup(name)
            self.settings.setValue("fromTime", fromEdit.dateTime())
            self.settings.setValue("toTime", toEdit.dateTime())
            self.settings.setValue("every", every.value())
            self.settings.setValue("record", checkBox.isChecked())
            self.settings.setValue("daily", daily.isChecked())
            self.settings.endGroup()
            every.setToolTip(f"Record every {every.value()} hours from the start time")

        inPipe, outPipe = multiprocessing.Pipe()
        shape = multiprocessing.Array('i', [0, 0])
        proc = Processor(cap, shape, self.tolerance, ids, encodings, inPipe, self.shared, node)
        thread = Thread(cId, shape, outPipe, self.shared, ard, name=name)
        closeBtn.clicked.connect(thread.start_stop)
        checkBox.clicked.connect(send)
        every.valueChanged.connect(send)
        fromEdit.dateTimeChanged.connect(send)
        toEdit.dateTimeChanged.connect(send)
        thread.change.connect(self.change)
        thread.outLabel.connect(self.setLabel)
        thread.out.connect(self.processType)
        QMetaObject.connectSlotsByName(self)

        return thread, proc

    def startCamera(self):
        """
        Slot used to Start all the cameras
        :return: Nothing
        """
        self.enableBtns(False)
        try:
            f = open(encFile, 'rb')
            lenBar = pickle.load(f)
            for i in range(lenBar):
                data = pickle.load(f)
                ids.append(data[0])
                encodings.append(data[1])
                self.setProgress(lenBar, i + 1)
            f.close()
        except FileNotFoundError or EOFError:
            debug(2, f"Encodings file '{encFile}' not found, did you forget to run Encode.py??")
            pass

        try:
            global temp
            temp = pickle.load(open(tempFile, 'rb'))
        except FileNotFoundError or EOFError:
            debug(1, "No previous records.")

        self.stopBtn.setEnabled(True)
        if self.startBtn.text() == "Restart":
            self.readKoskos()
            self.setupCams()

        for camera, proc, thread in zip(self.cameras, self.processes, self.threads):
            fr = camera.findChild(QDateTimeEdit, u'fromEdit').dateTime()
            to = camera.findChild(QDateTimeEdit, u'toEdit').dateTime()
            ev = camera.findChild(QSpinBox, u'every').value()
            proc.start()
            thread.start()
            # thread.setPid(proc.pid)
            thread.record(fr, to, ev, camera)

    def change(self, cId, p):
        """
        Slot - Change the scene of the camera view
        :param cId: int - Camera ID
        :param p: QImage - Processed frame
        :return: Nothing
        """
        cameraView = self.findChild(QGraphicsView, u"cameraView{}".format(cId))
        scene = self.findChild(QGraphicsScene, u"scene{}".format(cId))
        pix = QPixmap.fromImage(p.scaled(cameraView.size() - QtCore.QSize(2, 2)))
        scene.clear()
        scene.addPixmap(pix)
        cameraView.setScene(scene)

    def stop(self):
        """
        Slot - Stop all the cameras
        :return: Nothing
        """
        # self.shared = False
        for proc, thread in zip(self.processes, self.threads):
            if thread.isRunning():
                thread.terminate()
            if proc.is_alive():
                proc.terminate()
        self.stopBtn.setEnabled(False)
        if temp:
            pickle.dump(temp, open(tempFile, 'wb'))
        self.startBtn.setText("Restart")
        self.startBtn.setEnabled(True)
        self.config.setEnabled(True)

    def setLabel(self, text):
        """
        Slot - Print the current processed ID
        :param text: str - ID
        :return: Nothing
        """
        self.outLabel.setText(text)

    def processType(self, regid, img, dist, name):
        """
        Slot - The algorithm for determining the type of the entrance
        :param name: str - Name of the sender
        :param regid: int - The processed ID
        :param img: np.array - The image of the taken ID
        :param dist: float - The distance of the detected ID to the closest registered ID
        :return: Nothing
        """
        ri = int(regid)
        if ri in temp:
            tp, ti = temp[ri]
            t = (time.time() - ti) // 3600
            if tp == 1:
                if 6 <= t <= 14:
                    self.addItem(regid, 3, img, dist, name)
                elif t > 14:
                    if time.localtime(time.time() + 15 * 60).tm_hour in timeIn:
                        self.addItem(regid, 1, img, dist, name)
                else:
                    return
            elif tp == 3:
                if t >= 15:
                    if time.localtime(time.time() + 15 * 60).tm_hour in timeIn:
                        self.addItem(regid, 1, img, dist, name)
                else:
                    return
        else:
            if time.localtime(time.time() + 15 * 60).tm_hour in timeIn:
                self.addItem(regid, 1, img, dist, name)
            else:
                self.addItem(regid, 3, img, dist, name)

    def get_image(self, index):
        """
        Slot - Show the image of the logged ID and the original image of tha ID if it does exist
        :param index: int - The index in the table
        :return: Nothing
        """
        index = self.filter_proxy_model.mapToSource(index)
        i = self.model.item(index.row(), 0).text()
        d = self.model.item(index.row(), 2).text()
        d1 = i + '-' + d.split('-')[1].strip().replace(':', '-') + ".jpeg"
        d2 = d.split('-')[0].strip().replace('/', '-')
        path = os.path.join(os.getcwd(), LOGDIR, d2, d1)
        orig = self.encPath.text()
        if orig != "" and os.path.isdir(orig):
            try:
                path2 = os.path.join(orig, i)
                path2 = os.path.join(path2, os.listdir(path2)[0])
                if os.path.exists(path2):
                    os.system('start ' + path2 + '&')
                else:
                    QMessageBox.warning(None, "Error", "No base file found.", QMessageBox.Ok)
            except FileNotFoundError:
                QMessageBox.warning(None, "Error", "No base file found.", QMessageBox.Ok)
        os.system('start ' + path + '&')

    def addItem(self, regid, typ, img=None, dist=0.0, name='', date=None):
        """
        Add the detected ID to the table and save it in the log file
        :param name: str - Name of the Camera
        :param regid: int - The detected ID
        :param typ: int = Type of the entrance
        :param img: np.array - Detected image
        :param dist: float - The distance to the closest ID
        :param date: str - Date used in loading the lof file
        :return: Nothing
        """
        self.outLabel.setText(regid)
        date = QtCore.QDateTime().currentDateTime() if date is None else date
        dItem = QStandardItem(date.toString("dd/MM/yyyy - hh:mm:ss")) if type(date) is not str else QStandardItem(date)
        items = [QStandardItem(str(regid)), QStandardItem(str(typ)), dItem, QStandardItem(str("{:.2f}".format(dist)))]
        self.model.appendRow(items)
        self.attendanceTable.scrollToBottom()

        if img is not None:
            temp[int(regid)] = (typ, time.time())
            path = self.savePath.text() + '/' + name + '/'
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except PermissionError:
                    debug(3, f"Can't save to this location {path}, Permission denied")
                    return
            file_save((regid, typ, date.toString("dd/MM/yyyy\thh:mm:ss")))
            file_save((regid, typ, date.toString("dd/MM/yyyy\thh:mm:ss")), path + date.toString("dd-MM-yyyy") + '.txt')
        if img is not None and DEBUG:
            if not os.path.exists(LOGDIR):
                os.mkdir(LOGDIR)
            path = os.path.join(LOGDIR, date.toString('dd-MM-yyyy'))
            if not os.path.exists(path):
                os.mkdir(path)
            cv2.imwrite(f"{path}/{regid}-{date.toString('hh-mm-ss')}.jpeg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    def enableBtns(self, en):
        """
        Enable and disable some buttons
        :param en: bool - En of Dis
        :return: Nothing
        """
        self.startBtn.setEnabled(en)
        self.stopBtn.setEnabled(en)
        self.config.setEnabled(en)

    def setProgress(self, lenBar, i):
        """
        Slot - Set the progress
        :param lenBar: int - The length of the bar
        :param i: int - The current index
        :return: Nothing
        """
        self.progressBar.setMaximum(lenBar)
        self.progressBar.setValue(i)

    def closeEvent(self, arg__1: QtGui.QCloseEvent):
        """
        Cleanup before closing
        :param arg__1: Event
        :return: Nothing
        """
        self.stop()
