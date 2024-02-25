import cv2
import time
import requests
import numpy as np
import base64
import json
from flask import Flask, request
from flask_restful import Resource, Api

print("Connecting to Camera Stream")
stream_url = "http://10.194.21.169:8080/video"

path = "calibration_images/image{}.png"

app = Flask(__name__)
api = Api(app)

positionglb = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,1]]
positionstamp = 0

distance = 0
rssi = 0
def new_image():
    rsp = requests.get(stream_url, stream=True)

    if rsp.status_code == 200:
        bytes1 = bytes()
        for chunk in rsp.iter_content(chunk_size = 8192):
            bytes1+= chunk
            a = bytes1.find(b'\xff\xd8')
            b = bytes1.find(b'\xff\xd9')
            if a != -1 and b != -1:
                img = bytes1[a:b+2]
                img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
                img = cv2.imencode(".bmp", img)[1].tobytes()
                imgstring = base64.b64encode(img).decode('ascii')
                return imgstring
    return -1

class Camera(Resource):
    def get(self):
        return {'image': new_image(), 'time': time.time()}

class Position(Resource):
    def get(self):
        global positionglb
        global positionstamp
        return {'pose': positionglb, 'time': positionstamp};
    def post(self):
        global positionglb
        global positionstamp
        json_data = json.loads(request.get_json(force=True))
        positionglb = json_data['pose']
        return {'pose': positionglb, 'time': positionstamp}

class RSSI(Resource):
    def get(self):
        global distance
        global rssi
        return {'distance': distance, 'rssi': rssi}
    def post(self):
        global distance
        global rssi
        json_data = json.loads(request.get_json(force=True))
        distance = json_data['distance']
        rssi = json_data['rssi']
        return {'distance': distance, 'rssi': rssi}

api.add_resource(Camera, '/camera')
api.add_resource(Position, '/pose')
api.add_resource(RSSI, '/rssi')

if __name__ == '__main__':
    app.run(host = '10.192.173.150', debug = True)
