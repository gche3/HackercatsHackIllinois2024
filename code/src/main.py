import time

import requests

from robot_client import MotionClient
from purepursuit import PurePursuit

from camera_server.server_api import server_get

if __name__ == "__main__":
    while True:
        rssi_info = server_get("/rssi")
        print("waiting", rssi_info)
        if rssi_info['distance'] > 1:
            break
        time.sleep(1)
    while True:
        rssi_info = requests.get(server_url+"/rssi").json()
        print("primed", rssi_info)
        if rssi_info['distance'] <= 1:
            break
        time.sleep(1)

    robot = MotionClient()
    robot.startup()
    def get_pose():
        return robot.get_pos()

    path1 = [(0, 0), (0.5, 0), (0.5, 0.5), (0.25, 0.5)]
    path2 = [(0.5, 0.5), (0, 0.5), (0, 0), (0.25, 0)]
    kv = 1.5
    radius = 0.1
    speed = 1

    for path in [path1, path2]:
        follower = PurePursuit(path, radius, speed, kv)
        while True:
            cur = get_pose()
            done, cmd = follower.step(cur)
            if done:
                break
            #cmd = [cmd[0], cmd[1] * -1]
            print(cmd, cur)
            print(follower.get_lookahead(cur))
            robot.motor_command(cmd[0] + cmd[1], cmd[0] - cmd[1])

        robot.motor_command(0, 0)
