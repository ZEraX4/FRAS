import argparse
import os
import pickle
import sys

import cv2
import progressbar
from face_recognition import face_locations, face_encodings
from face_recognition.face_detection_cli import image_files_in_folder

from utils import debug

ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                             description="Encode video files or images", epilog=""
                                         "You are supposed to have a training directory that contain video files or\n"
                                         "images folders of the IDs you want to encode, Then you can run the script\n"
                                         "with -d for specifing the training directory and -v or -i or both,\n\n"
                                         "Note: You have to specify -o for -p, -s, -r options if it is not the default"
                                         "\nname (enc.dat), Here are some examples: \n\n"
                                         "\tpython Encode.py -d Train -i # encode images only in 'Train' directory\n"
                                         "\tpython Encode.py -d Train -v # encode videos only in 'Train' directory\n"
                                         "\tpython Encode.py -d Train -v # encode both videos and images in 'Train'\n"
                                         "\tpython Encode.py -p          # print the contents of the enc.dat file if "
                                         "exists\n "
                                         "\tpython Encode.py -s 6669     # search if ID 6669 in enc.dat file\n"
                                         "\tpython Encode.py -r 6669     # remove ID 6669 from enc.dat file")
ap.add_argument("-d", "--dir", help="Training directory.")
ap.add_argument("-o", "--out", help="Encoded data file.")
ap.add_argument("-r", "--remove", type=int, help="Remove a specified encoding.")
ap.add_argument("-v", "--videos", action="store_true", help="Use videos files.")
ap.add_argument("-i", "--images", action="store_true", help="Use images files.")
ap.add_argument("-p", "--print", action="store_true", help="Print the contents of the .dat file.")
ap.add_argument("-s", "--search", help="Search for a specified id in -p output.")
args = vars(ap.parse_args())


def check(code):
    return str(code) in ids


def delete(code):
    while 1:
        try:
            idx = ids.index(str(code))
            del ids[idx]
            del encodings[idx]
        except ValueError:
            break


def encFile(image, known=False):
    face = cv2.resize(image, (320, 240))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    face_location = (0, face.shape[1], face.shape[0], 0) if known else face_locations(face)
    if not len(face_location):
        return None
    return face_encodings(face, face_location, model='small')[0]


def enc_vid(video):
    ee = list()
    ii = list()

    cap = cv2.VideoCapture(video)
    numframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    name = str.split(video, '.')[-2].split('\\')[-1]
    with progressbar.ProgressBar(max_value=numframes, redirect_stdout=True) as bar:
        for i in range(numframes):
            bar.update(i)

            grabbed, frame = cap.read()
            if not grabbed:
                break

            en = encFile(frame)
            if en is not None:
                ee.append(en)
                ii.append(name)
    return ii, ee


def encFromFolder(folder, known=False):
    ee = list()
    ii = list()

    files = image_files_in_folder(folder)
    with progressbar.ProgressBar(max_value=len(files), redirect_stdout=True) as bar:
        for i, image in enumerate(files):
            bar.update(i)
            face = cv2.imread(image)
            name = str.split(image, '\\')[-2]
            print(f'{name} Encoded.')
            en = encFile(face, known)
            if name is not None and en is not None:
                ee.append(en)
                ii.append(name)
            else:
                debug(2, f"No face found in {image}, removing...")
                os.remove(image)
    return ii, ee


if __name__ == "__main__":
    dat_file = args['out'] if args['out'] is not None else 'enc.dat'
    done = False
    ids = list()
    encodings = list()

    try:
        f = open(dat_file, 'rb')
        lenBar = pickle.load(f)
        for i in range(lenBar):
            data = pickle.load(f)
            ids.append(data[0])
            encodings.append(data[1])
        f.close()
    except FileNotFoundError or EOFError:
        debug(2, f"Output file '{dat_file}' does not exist, just FYI :)")
        pass

    if args['remove']:
        if check(args['remove']):
            debug(2, f"Deleting {args['remove']}!")
            delete(args['remove'])
            done = True
        else:
            debug(2, f"{args['remove']} does not exist.")

    elif args['print']:
        if len(ids) > 0:
            if args['search']:
                try:
                    ids.index(args['search'])
                    debug(1, f"{args['search']} found!!")
                except ValueError:
                    debug(2, f"{args['search']} does not exist.")
            else:
                print(set(ids))
        else:
            debug(2, f"{dat_file} is empty or not existed.")

    else:
        if args['dir'] is None:
            debug(3, "You need to specify a training dir -d, exiting.")
            sys.exit(0)
        else:
            train_dir = args['dir']
        if not os.path.isdir(train_dir):
            debug(3, f"'{train_dir}' folder does not exits.")
            sys.exit(0)

        if args['videos'] or args['images']:
            if args['videos']:
                for d in os.listdir(train_dir):
                    path = os.path.join(train_dir, d)
                    dd = d.split('.')[0]
                    if not os.path.isdir(path) and d.split('.')[-1] == 'mp4':
                        if check(dd):
                            debug(2, f"{dd} is already existed, skipping...")
                        else:
                            debug(1, f"Openning video file: {d}...")
                            i, e = enc_vid(path)
                            ids.extend(i)
                            encodings.extend(e)
                            done = True

            if args['images']:
                for d in os.listdir(train_dir):
                    if os.path.isdir(os.path.join(train_dir, d)):
                        try:
                            i = int(d)
                            if not check(d):
                                path = os.path.join(train_dir, d)
                                if not os.path.isdir(path):
                                    continue
                                idt, enc = encFromFolder(path, False)
                                ids.extend(idt)
                                encodings.extend(enc)
                                done = True
                            else:
                                debug(2, f"{d} is already existed, skipping...")
                        except ValueError:
                            debug(2, f'{d} Is not an id folder.')
                            continue
        else:
            ap.print_help()
            sys.exit(0)

    if done:
        debug(1, f"Writing enodings to {dat_file}...")
        with open(dat_file, 'wb') as f:
            pickle.dump(len(ids), f)
            for i, v in zip(ids, encodings):
                pickle.dump((i, v), f)
            f.close()
        debug(1, "Done.")

