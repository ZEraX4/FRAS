import time
from multiprocessing import Process
from urllib.parse import urlparse

import cv2
import face_recognition
import numpy as np
from imutils.video import WebcamVideoStream

from utils import debug

# Number of tries before restarting the connection
MAX_TRIES = 5
# Number of frames to use for checking the correct ID
MAX_FRAME = 1
# Camera shape
CAM_SHAPE = (0, 0)


class Processor(Process):
    """
    The brain of this program
    """
    def __init__(self, cap, shape, tolerance, cods, encs, inPipe, shared=None, node=None):
        """
        Constructor
        :param cap: str - Path of the camera or port if it is a node
        :param shape: tuple(int, int) - Shape of the camera frame
        :param tolerance: float - How much distance to consider it a match
        :param cods: List() - list of IDs used for comparing
        :param encs: List() - List of encodings used for comparing
        :param inPipe: multiprocessing.Pipe() - Used for sending frames and result
        :param shared: multiprocessing.Value() - Boolean used to stop the process
        :param node: Boolean - Use a node
        """
        super(Processor, self).__init__()
        self.cap = cap
        self.shape = shape
        self.tolerance = tolerance
        self.ids = cods
        self.encs = encs
        self.inPipe = inPipe
        self.shared = shared
        self.node = node
        self.tries = 0
        self.lastface = None

    def run(self):
        """
        Main routine
        :return: Nothing
        """
        global CAM_SHAPE

        debug(1, f"Process {self.pid} has started")

        if self.node is not None:
            import imagezmq
            path = self.node[1]
            rec = imagezmq.ImageHub(f"tcp://*:{path}")
        else:
            try:
                self.cap = int(self.cap)
                path = self.cap
            except ValueError:
                path = urlparse(self.cap).netloc

                try:
                    path = path[path.rfind('@') + 1:]
                except ValueError:
                    pass
        while True:
            if self.node is None:
                debug(1, f"Connecting to camera: {path}...")
                cap = WebcamVideoStream(self.cap).start()
                if not cap.stream.isOpened():
                    debug(3, f"Can't connect to camera: {path}, Retrying...")
                    continue
            else:
                debug(1, f"Waiting for node on Port: {path}...")
            break

        while True:
            matched = "Unknown"
            dist = 0
            face_tries = 0

            while True:
                if self.node:
                    _, frame = rec.recv_image()
                else:
                    frame = cap.read()

                if frame is None:

                    if self.tries > MAX_TRIES:
                        debug(3, f"Lost connection to: {path}")
                        break

                    self.tries += 1
                    debug(2, f"Retrying {self.tries}:{path}...")
                    time.sleep(1)
                    continue

                if CAM_SHAPE == (0, 0):
                    CAM_SHAPE = (frame.shape[1], frame.shape[0])

                    with self.shape:
                        self.shape.get_lock()
                        self.shape[:] = list(CAM_SHAPE)[:]

                rgb_frame = frame[:, :, ::-1]
                # Change the model to 'cnn' if you have a gpu for faster detection
                face_locations = face_recognition.face_locations(rgb_frame, model='hog')
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, model='small')

                if len(face_encodings) < 1:
                    matched = "Unknown"

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    color = (0, 0, 255)

                    if self.encs:

                        matches = face_recognition.compare_faces(self.encs, face_encoding,
                                                                 tolerance=self.tolerance.value)
                        face_distances = face_recognition.face_distance(self.encs, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index]:
                            name = self.ids[int(best_match_index)]
                            dist = face_distances[best_match_index]

                            if name == self.lastface and face_tries == MAX_FRAME:
                                color = (0, 255, 0)
                                matched = name
                                face_tries = 0

                            elif name == self.lastface and face_tries < MAX_FRAME:
                                color = (255, 0, 0)
                                face_tries += 1
                                self.lastface = name
                                matched = "Pending"

                            else:
                                matched = "Unknown"
                                face_tries = 0
                                self.lastface = name
                        else:
                            matched = "Unknown"

                    cv2.rectangle(frame, (left, top), (right, bottom), color, 1)
                    cv2.rectangle(frame, (left, bottom + 20), (right, bottom), color, cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, matched, (left + 6, bottom + 15), font, 0.7, (255, 255, 255), 1)

                if self.node is not None:
                    rec.send_reply(bytes(matched, encoding='utf-8'))
                p = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.inPipe.send((p, matched, dist))

            if self.tries > MAX_TRIES:
                self.tries = 0
                time.sleep(1)
                continue

            debug(1, "Exiting...")
            self.inPipe.send(None)
            break

    def terminate(self) -> None:
        """
        Cleanup stuff
        :return:
        """
        debug(1, f"Process {self.pid} is closing...")
        self.inPipe.close()
        super(Processor, self).terminate()
