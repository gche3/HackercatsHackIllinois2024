import time

import matplotlib.pyplot as plt
import numpy as np

from robot_client import MotionClient

robot = MotionClient()
robot.startup()

plt.ion()
plt.figure(0)

while True:
    plt.xlim(-3, 3)
    plt.ylim(-3, 3)
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

    x0 = np.array(robot.get_pos())
    print(x0)
    plt.pause(0.05)
