 # FRAS - Face Recognition Attendance System
 FRAS is a Server-Node based small attendance system using face recognition.
 
 This application is a small use case of the [face_recognition]() library which is based on [dlib]()
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
 
 NOTE: There are other useful option in `Encode.py` script you can find them in the `-h` help parameter.
 
 Here's an example:
 ```bash
 python Encode.py -d Train -i -v
 ```
 After that, you can run the main programe by calling `Main.py`.

 The first run of the application will require you to set up a config file

 ## Licence:
 [MIT](https://choosealicense.com/licenses/mit/)