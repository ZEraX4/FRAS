 # FRAS - Face Recognition Attendance System
 FRAS is a Server-Node based small attendance system using face recognition.
 
 This application is a small use case of the [face_recognition](https://github.com/ageitgey/face_recognition) 
 library which is based on [dlib](http://dlib.net/)
 ## Requirements:
 Make sure you have the necessary packages by doing this:
 ```bash
 pip install -r requirements.txt 
 ```
 ## How to use:
 First, you need to have a folder that contains either video files or image folders of the faces
 you want to encode, so you can use them in the application, Like this for example:
```bash
C:\USERS\ZERAX\DESKTOP\FRAS\TRAIN
│   6669.mp4
│
└───6669
        0.jpeg
        1.jpeg
        10.jpeg
        100.jpeg
```

 Then you can use `Encode.py` script with `-d [train_directory]` parameter taking the train directory that include the 
 files you want to encode, and `-v` or `-i` parameters for videos and images respectivley (you may use 
 both of them).

 This will create an encoding file called `enc.dat` file containing the encodings (you may change the 
 name of the file by adding `-o [OUT]` parameter but then you will need to modify the `MainDialog.py` 
 script to account for that).
 
 NOTE: There are other useful options in `Encode.py` script you can find them in the `-h` help parameter.
 
 Here's an example:
 ```bash
 python Encode.py -d Train -i -v
 ```
 After that, you can run the main programe by calling `Main.py`.

 The first run of the application will require you to set up a config file, You will be
 welcomed by the configuration window where you can add an ip camera, an internal 
 camera, or a node.

 **Add Camera:** will add 3 fileds:

 - Camera Name: display name and will be used as the folder name where the logs will be
   saved.
 - Camera IP: accept an ip, or the number of the camera.
 - Arduino IP: this filed is optional, if you want to use it you need and arduino 
   connected to the network and accept http requests, the application will send it 
   a request whenever a face gets recognized.
   
 **Add Node:** will add 2 fields:

 - Node Name: display name and will be used as the folder name where the logs will be
   saved.
 - Node Port: used by the server to listen on (each node must have a unique port).

 NOTE: Node is reffered to a small computer with a camera like raspberry pi 
 for example running the `Node.py` script.

 ###The rest of documentation is under construction but if you want to try, the application is self-explanatory with hints for the ambigous control options. 
 ## Licence:
 [MIT](https://choosealicense.com/licenses/mit/)