import time
from robot_client import MotionClient

robot = MotionClient()
robot.startup()

powers = [0.7, 0.8, 0.9, 1]

for power in powers:
    input(f"Enter to try power {power}: ")
    robot.motor_command(-power, power)
    time.sleep(2)
    robot.motor_command(0, 0)
