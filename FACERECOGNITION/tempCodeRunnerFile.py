import os
import pickle
import face_recognition
import cvzone
import cv2
import numpy as np
import json
import paho.mqtt.client as mqtt
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
import imutils

# MQTT broker configuration
mqtt_broker = "159.223.61.133"
mqtt_port = 1883
mqtt_topic = "door/status"
mqtt_username = "mecharoot"
mqtt_password = "mecharnd595"

cred = credentials.Certificate(
    "D:/FACERECOGNITION/faceattendacerealtime-45f98-firebase-adminsdk-xkzbo-184093dad7.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendacerealtime-45f98-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendacerealtime-45f98.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('D:/FACERECOGNITION/Resources/background.png')

# Importing the mode images into a list
folderModePath = 'D:/FACERECOGNITION/Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Load the encoding file
print("Loading Encode File ...")
file = open('D:/FACERECOGNITION/EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'C:/Users/Febrian Zulmi/Downloads/haar-cascade-files-master/haar-cascade-files-master/haarcascade_frontalface_alt2.xml')

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(mqtt_username, mqtt_password)
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.loop_start()

# MQTT callback function for when a message is received


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    print("Received message:", payload)

    # parse the JSON payload
    data = json.loads(payload)
    door_status = data["door_status"]

    # process the door status
    if door_status == "1":
        print("Pintu Terbuka: Suhu anda aman")
    elif door_status == "0":
        print("Pintu Tertutup: Suhu anda terlalu tinggi")
    else:
        print("Invalid door status")


# set the callback function
mqtt_client.on_message = on_message

# subscribe to MQTT topic
mqtt_client.subscribe(mqtt_topic)

# start the MQTT loop to handle incoming messages
mqtt_client.loop_start()

# initialize last_message_time
last_message_time = time.time()

modeType = 0
counter = 0
id = -1
imgStudent = []

fever_temperature_threshold = 38.0

while True:
    success, img = cap.read()

    # Perform face detection
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray_img, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        face_roi = gray_img[y:y+h, x:x+w]

        # Convert the detected face region to RGB for face recognition
        face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_GRAY2RGB)

        # Perform face recognition on the detected face
        encodeFace = face_recognition.face_encodings(face_rgb)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        for encodeFace, faceLoc in zip(encodeFace, faces):
            matches = face_recognition.compare_faces(
                encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(
                encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                # print("Known Face Detected")
                # print(studentIds[matchIndex])
                gray16_high_byte = (np.right_shift(img, 0)).astype('uint8')
                gray16_low_byte = (np.left_shift(
                    img, 0) / 256).astype('uint16')
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                gray16_roi = np.array(gray16_high_byte, dtype=np.uint16)
                gray16_roi = gray16_roi * 256
                gray16_roi = gray16_roi | gray16_low_byte
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                temperature = np.mean(gray16_roi)

                # konversi fahrenheit ke celcius calculate the average temperature based on the pixel values in the face_roi
                temperature = ((temperature - 32) - (5/9)) / 1000
                id = studentIds[matchIndex]

                if counter == 0:

                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    modeType = 1
                    if temperature < fever_temperature_threshold:
                        # white text: normal temperature
                        cv2.putText(imgBackground, "{0:.1f} C".format(temperature), (275, 400),
                                    cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 255, 0), 2)
                        # set door status to open
                        door_status = 1
                        counter = 1
                    else:
                        # - red text + red circle: fever temperature
                        cv2.putText(imgBackground, "{0:.1f} C".format(temperature), (275, 400),
                                    cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 255), 2)
                        modeType = 0

        if counter != 0:
            if counter == 1:
                if temperature < fever_temperature_threshold:
                    # white text: normal temperature
                    cv2.putText(imgBackground, "{0:.1f} C".format(temperature), (275, 400),
                                cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 255, 0), 2)
                    # set door status to open
                    door_status = 1
                else:
                    # - red text + red circle: fever temperature
                    cv2.putText(imgBackground, "{0:.1f} C".format(temperature), (275, 400),
                                cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 255), 2)
                    modeType = 0
                # Get the Data
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                # Get the Image from the storage
                blob = bucket.get_blob(f'Images/{id}.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                # Update data of attendance
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                   "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (
                    datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)

                if secondsElapsed > 15:
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance'] += 1
                    ref.child('total_attendance').set(
                        studentInfo['total_attendance'])
                    ref.child('temperature').set(
                        "{0:.1f} 'C".format(temperature))
                    ref.child('last_attendance_time').set(
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 +
                                  414] = imgModeList[modeType]

            if modeType != 3:

                if 10 < counter < 20:
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 +
                              414] = imgModeList[modeType]

                if counter <= 10:

                    cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['temperature']), (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    (w, h), _ = cv2.getTextSize(
                        studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                counter += 1

                if counter >= 20:

                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgStudent = []
                    imgBackground[44:44 + 633, 808:808 +
                                  414] = imgModeList[modeType]

                # Check if it's time to send the MQTT message
                if (time.time() - last_message_time >= 10):
                    # Create JSON payload
                    payload = json.dumps({"door_status": str(door_status)})

                    # Publish door status to MQTT broker
                    mqtt_client.publish(mqtt_topic, payload)

                    # Update last_message_time
                    last_message_time = time.time()

                # Show the final result with overlays
                cv2.imshow("Face Attendance", imgBackground)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
mqtt_client.loop_stop()
mqtt_client.disconnect()
