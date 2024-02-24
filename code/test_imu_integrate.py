import time

import requests
import numpy as np

from src.utils.plot_ringbuffer import ArrayRingBuffer

#import matplotlib.pyplot as plt
from plot_wrapper import InteractiveMatplotlibWrapper
from motionlib import vectorops as vo, so3, se3

plt = InteractiveMatplotlibWrapper()
plt.start()
plt.figure(0)

v = np.zeros(3)
pose = so3.identity()
v_buf = ArrayRingBuffer(100, 4)
pose_buf = ArrayRingBuffer(100, 9)

accel_zero = np.zeros(3)
gyro_zero = np.zeros(3)
accel_zero_ticks = 100
gyro_zero_ticks = 500
timestep = 0

latest = 0
latest_gyro = 0

while True:
    x = requests.get("http://10.194.232.216:8080/sensors.json")
    #print(x.json())
    _accels = x.json()['accel']['data']
    _gyros = x.json()['gyro']['data']

    times = np.array([dat for dat, _ in _accels]) / 1000
    accels = np.array([dat for _, dat in _accels])
    gyro_t = np.array([dat for dat, _ in _accels]) / 1000
    gyro_dat = np.array([dat for _, dat in _accels])

    # The index of the next reading to integrate.
    # might equal length of array if there's no more readings to integrate.
    idx = np.searchsorted(times, latest)+1
    gyro_idx = np.searchsorted(gyro_t, latest_gyro)+1

    for i in range(idx, len(times)):
        accel_time = times[i]
        while latest_gyro < accel_time:
            if gyro_idx == len(gyro_t):
                break
            gyro_dt = gyro_t[gyro_idx] - gyro_t[gyro_idx-1]
            gyro_step = gyro_dat[gyro_idx, :] * gyro_dt
            pose = so3.mul(so3.from_moment(gyro_step), pose)
            latest_gyro = gyro_t[gyro_idx]
            gyro_idx += 1
            
        accel = accels[i, :]
        if timestep == accel_zero_ticks:
            accel_zero /= accel_zero_ticks
        elif timestep < accel_zero_ticks:
            accel_zero += accel
        else:
            accel -= so3.mul(pose, accel_zero)
            dt = times[i] - times[i-1]
            v += accel * dt
            v_buf.add_data([times[i], *v])
            pose_buf.add_data([times[i], *pose])
        timestep += 1

    latest = times[-1]
    while gyro_idx < len(gyro_t):
        gyro_dt = gyro_t[gyro_idx] - gyro_t[gyro_idx-1]
        gyro_step = gyro_dat[gyro_idx, :] * gyro_dt
        pose = so3.apply(so3.from_moment(gyro_step), pose)
        gyro_idx += 1
    latest_gyro = gyro_t[-1]

    plt.clf()
    dat = v_buf.get_data()
    plt.plot(dat[:, 0], dat[:, 1], label="x")
    plt.plot(dat[:, 0], dat[:, 2], label="y")
    plt.plot(dat[:, 0], dat[:, 3], label="z")
    plt.legend()
    time.sleep(0.05)
    print(pose)

plt.stop()
