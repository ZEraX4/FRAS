import os
import time

import requests
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QImage, QIcon
from PyQt5.QtWidgets import QPushButton, QCheckBox
from numpy.core.multiarray import ndarray
from qimage2ndarray import array2qimage
from requests.adapters import HTTPAdapter
import cv2

from utils import get_time, debug

# Used for terminating the connection to the arduino so it does not hang the program
DEFAULT_TIMEOUT = 1
# Where the save the recording
REC_PATH = 'Recordings'
# FPS of the recorded videos
REC_FPS = 5


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


http = requests.Session()
# Mount it for both http and https usage
adapter = TimeoutHTTPAdapter()
http.mount("https://", adapter)
http.mount("http://", adapter)


class Thread(QThread):
    """
    Thread used as a middle man between the process and the main program
    """
    change = pyqtSignal(int, QImage)
    face = pyqtSignal(ndarray)
    out = pyqtSignal(str, ndarray, float, str)
    outLabel = pyqtSignal(str)
    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    def __init__(self, cId, shape, outPipe, shared, ard, name=''):
        """
        Constructor
        :param cId: str - ID of the camera
        :param shape: tuple(int, int) - Shape of the camera frame
        :param outPipe: multiprocessing.Pipe() - Used for receiving frames from the process
        :param shared: multiprocessing.Value() - Boolean value to start or stop the thread
        :param ard: str - URL of the arduino
        :param name: str - Name of the camera
        """
        super(Thread, self).__init__()
        self.id = ""
        self.lastFace = None
        self.tries = 0
        self.cId = cId
        self.name = name
        self.shape = shape
        self.shared = shared
        self.outPipe = outPipe
        self.ard = ard
        # self.pid = None
        self.paused = False
        self.lastTime = 0
        self.vid = None
        self.rec = False
        self.daily = False
        self.every = 0
        self.startedRec = False
        self.fromTime = None
        self.toTime = None
        self.button = None

    # def setPid(self, pid):
    #     self.pid = psutil.Process(pid)

    def record(self, d1, d2, ev, s=None):
        """
        Record function
        :param d1: QDateTime() - Start time
        :param d2: QDateTime() - End time
        :param ev: int - Record again after thing number of hours
        :param s: QObject() - Caller of this function
        :return:
        """
        sender = self.sender().parent() if not s else s
        self.button = sender.findChild(QPushButton)
        check = sender.findChild(QCheckBox, u"record")
        self.daily = sender.findChild(QCheckBox, u"daily").isChecked()
        self.every = ev
        if check.isChecked():
            self.fromTime = d1
            self.toTime = d2
            self.rec = True
            self.button.setEnabled(False)
        else:
            self.fromTime = None
            self.toTime = None
            self.rec = False
            self.button.setEnabled(True)

    def start_stop(self, btn=None, stop=True):
        """
        Start or stop the recording
        :param btn: QPushButton() - Used to check if the user pressed the button or not
        :param stop: Boolean - Stop the recording
        :return: Nothing
        """
        sender = self.sender() if not btn else btn
        if self.paused and stop:
            sender.setIcon(QIcon('Icons/play.png'))
            self.paused = False
            self.startedRec = False
            self.vid.release()
            debug(1, f"Stopped recording on cam: {self.name}.")
        else:
            CAM_SHAPE = tuple(self.shape)
            if CAM_SHAPE == (0, 0):
                debug(2, "You need to start the camera first.")
                return
            sender.setIcon(QIcon('Icons/pause.png'))
            if self.vid:
                self.vid.release()
            if not os.path.exists(REC_PATH):
                os.mkdir(REC_PATH)
            self.vid = cv2.VideoWriter(f"{REC_PATH}/{get_time(file=True)}.avi", self.fourcc, REC_FPS, CAM_SHAPE)
            self.paused = True
            debug(1, f"Started recording on cam: {self.name}.")

    def run(self):
        """
        Main routine
        :return: Nothing
        """
        while self.shared.value:
            try:
                p = self.outPipe.recv()
            except EOFError:
                self.outPipe.close()
                break

            if p is None:
                break

            p1, n, dist = p

            if self.rec:
                cond1 = 0
                if self.every > 0:
                    t1 = self.fromTime.toSecsSinceEpoch()
                    cr = QDateTime.currentDateTime().toSecsSinceEpoch()
                    dur = (cr - t1) // 3600 // self.every
                    t1 = self.fromTime.addSecs(self.every*dur*3600)
                    t2 = self.toTime.addSecs(self.every*dur*3600)
                    cond1 = t1 <= QDateTime.currentDateTime() <= t2

                if self.daily:
                    cond = self.fromTime.time() <= QDateTime.currentDateTime().time() <= self.toTime.time() or cond1
                else:
                    cond = self.fromTime <= QDateTime.currentDateTime() <= self.toTime or cond1

                if cond:
                    if not self.startedRec and not self.paused:
                        self.startedRec = True
                        self.start_stop(self.button, False)
                else:
                    if self.startedRec:
                        self.start_stop(self.button)

            if self.paused:
                frame = cv2.cvtColor(p1, cv2.COLOR_RGB2BGR)
                cv2.putText(frame, get_time(), (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                self.vid.write(frame)

            p = array2qimage(p1)
            self.change.emit(self.cId, p)

            if n not in ["", "Unknown", "Pending"] and n != self.lastFace:
                try:
                    if self.ard:
                        http.get(self.ard)
                    self.lastTime = time.time()
                    self.lastFace = n
                    self.out.emit(n, p1, dist, self.name)
                    self.outLabel.emit(n)
                except IOError as e:
                    debug(3, f"{type(e).__name__} - Url: {self.ard}")
            elif time.time() - self.lastTime >= 2:
                self.lastFace = None

    def terminate(self) -> None:
        """
        Cleanup stuff
        :return:
        """
        if self.vid:
            self.vid.release()
            debug(1, f"Stopped recording on cam: {self.name}.")
