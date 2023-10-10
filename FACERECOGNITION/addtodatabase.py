
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate(
    "D:/FACERECOGNITION/faceattendacerealtime-45f98-firebase-adminsdk-xkzbo-184093dad7.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendacerealtime-45f98-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "321654":
        {
            "name": "Oppenheimer",
            "major": "Physics",
            "starting_year": 1927,
            "total_attendance": 7,
            "temperature": 0,
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
        
    "1306620081":
        {
            "name": "Rofid",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 0,
            "temperature": 0,
            "year": 3,
            "last_attendance_time": "2022-12-11 00:54:34"

        },
        
    "1306620014":
        {
            "name": "Nugraha",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 0,
            "temperature": 0,
            "year": 3,
            "last_attendance_time": "2022-12-11 00:54:34"

        },
        
    "130662002":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 0,
            "temperature": 0,
            "year": 3,
            "last_attendance_time": "2022-12-11 00:54:34"

        },
        

    "1306620032":
        {
            "name": "Febrian Zulmi",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 0,
            "temperature": 0,
            "year": 3,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}

for key, value in data.items():
    ref.child(key).set(value)
