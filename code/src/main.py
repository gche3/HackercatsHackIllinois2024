import time

import requests

from robot_client import MotionClient
from purepursuit import PurePursuit

from camera_server.server_api import server_get

robot = MotionClient()
robot.startup()
def get_pose():
    return robot.get_pos()

def main():

    kv = 1.5
    radius = 0.1
    speed = 1

    while True:
        rssi_info = server_get("/rssi")
        print("waiting", rssi_info)
        if rssi_info['distance'] > 1:
            break
        time.sleep(1)
    while True:
        rssi_info = server_get("/rssi")
        print("primed", rssi_info)
        if rssi_info['distance'] <= 1:
            break
        time.sleep(1)

    path1 = [(0, 0), (0.6, -0.9), (0.0, -1.5), (-0.6, -2.3)]

    for path in [path1]:
        follower = PurePursuit(path, radius, speed, kv)
        while True:
            cur = get_pose()
            done, cmd = follower.step(cur)
            if done:
                break
            robot.motor_command(cmd[0] + cmd[1], cmd[0] - cmd[1])

        robot.motor_command(0, 0)

    while True:
        rssi_info = server_get("/rssi")
        print("primed2", rssi_info)
        if rssi_info['distance'] > 1:
            break
        time.sleep(1)

    robot.motor_command(1, -1)
    time.sleep(1)
    path1 = [(-0.6, -2.3), (0.0, -1.5), (0.6, -0.9), (0.0, 0.0)]

    for path in [path1]:
        follower = PurePursuit(path, radius, speed, kv)
        while True:
            cur = get_pose()
            done, cmd = follower.step(cur)
            if done:
                break
            robot.motor_command(cmd[0] + cmd[1], cmd[0] - cmd[1])

        robot.motor_command(0, 0)
    while True:
        rssi_info = server_get("/rssi")
        print("waiting again", rssi_info)
        if rssi_info['distance'] <= 1:
            break
        time.sleep(1)

while True:
    main()

