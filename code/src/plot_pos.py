import time

import matplotlib.pyplot as plt
import numpy as np

from klampt.math import vectorops as vo, so3, se3

from robot_client import MotionClient
import requests
from camera_server.server_api import server_get

robot = MotionClient()
robot.startup()

plt.ion()
plt.figure(0)

pose_info = server_get("/pose")
prev_pose_time = pose_info['time']
time_offset = time.monotonic() - prev_pose_time
init_pose = np.array(pose_info['pose'])
R0 = so3.from_matrix(init_pose[:3, :3])
#print(init_pose)
R0_inv = so3.inv(R0)
#R0_inv = #(0, -1, 0, 0, 0, -1, 1, 0, 0)
t0 = init_pose[:3, 3]

def get_pose_slam(prev_pose_time):
    pose_info = server_get("/pose")
    pose_time = pose_info['time']
    time_offset = time.monotonic() - pose_time
    if time_offset > 5:
        print("Lost track")
        return (None, -1)
    pose = np.array(pose_info['pose'])
    #print(pose)
    R = so3.from_matrix(pose[:3, :3])
    t = vo.sub(pose[:3, 3], t0)
    print(t)
    print(pose[:3, :3])
    return ((so3.mul(R0_inv, R), t), pose_time)

def show_robot(pos, theta, R=0.1):
    x1 = pos + np.array([R*np.cos(theta), R*np.sin(theta)])
    plt.plot([pos[0], x1[0]], [pos[1], x1[1]])
    circle = plt.Circle(pos, 0.05, color='b')
    ax = plt.gca()
    ax.add_patch(circle)

while True:
    plt.clf()
    plt.xlim(-1, 1)
    plt.ylim(-3, 1)
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

    x0 = np.array(robot.get_pos())

    res, pose_time = get_pose_slam(prev_pose_time)
    if res is not None:
        prev_pose_time = pose_time
        #print(res)
        angle = so3.moment(res[0])[1]
        #show_robot(res[1][:2], angle)

    show_robot(x0[:2], x0[2])
    plt.pause(0.05)
