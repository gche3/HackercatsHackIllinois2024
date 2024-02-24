import cv2
import time
import requests
import numpy as np

#print('connecting to camera')
#cam = cv2.VideoCapture(0)
print('connecting to camera stream')
stream_url = "http://10.194.232.216:8080/video"

KEY_ESC = 27

img_counter = 0

path = "calibration_images/image{}.png"
response = requests.get(stream_url, stream=True)

if response.status_code == 200:
    #ret, image = cam.read()
    bytes = bytes()
    for chunk in response.iter_content(chunk_size=8192):
        bytes += chunk
        a = bytes.find(b'\xff\xd8')
        b = bytes.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes = bytes[b+2:]
            image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow('image', image)
            key = cv2.waitKey(1)
            if key == KEY_ESC:
                print("Esc")
                break
            if key == ord(' '):
                cv2.imwrite(path.format(img_counter), image)
                print(f"Image {img_counter}")
                img_counter += 1
