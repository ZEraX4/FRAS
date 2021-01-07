from datetime import datetime
from colorama import init


levels = {1: "INFO",
          2: "WARN",
          3: "EROR"}
colors = {1: '\033[32m',
          2: '\033[33m',
          3: '\033[31m',
          4: '\033[0m'}
DEBUG = True


def file_save(data, n=""):
    name = n if n != "" else 'log.txt'
    file = open(name, 'a+')
    regid, typ, dat = data
    text = f"{regid}\t{dat}\t{typ}\n"
    file.write(text)
    file.close()


def get_time(file=False):
    if file:
        return datetime.now().strftime("%d.%m.%Y - %H.%M.%S")
    return datetime.now().strftime("%d/%m/%Y - %H:%M:%S")


def debug(lvl, msg):
    init()
    if DEBUG:
        if lvl in levels:
            print(f"{colors[lvl]}[{levels[lvl]}][{get_time()}] " + msg + colors[4])
