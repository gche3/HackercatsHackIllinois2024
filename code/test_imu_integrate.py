import time

import rpyc
import requests
import numpy as np

from src.utils.plot_ringbuffer import ArrayRingBuffer

#import matplotlib.pyplot as plt
from plot_wrapper import InteractiveMatplotlibWrapper
from motionlib import vectorops as vo, so3, se3

#plt = InteractiveMatplotlibWrapper()
#plt.start()
#plt.figure(0)

v = np.zeros(3)
pose = so3.identity()
v_buf = ArrayRingBuffer(100, 4)
pose_buf = ArrayRingBuffer(100, 10)

accel_zero = np.zeros(3)
accel_zero_ticks = 100
timestep = 0

latest = 0

while True:
    x = requests.get("http://10.194.232.216:8080/sensors.json").json()
    #print(x.json())
    _accels = x['lin_accel']['data']
    _rots = x['rot_vector']['data']

    times = np.array([dat for dat, _ in _accels]) / 1000
    accels = np.array([dat for _, dat in _accels])

    rot_t = np.array([dat for dat, _ in _rots]) / 1000
    rot_dat = np.array([dat for _, dat in _rots])

    # We want to be right handed
    accels[:, 2] *= -1

    # The index of the next reading to integrate.
    # might equal length of array if there's no more readings to integrate.
    idx = np.searchsorted(times, latest)+1
    rot_idx = np.searchsorted(rot_t, latest)

    rot = rot_dat[rot_idx]
    rot_time = rot_t[rot_idx]
    rot_idx += 1

    raw_accel = accels[-1, :].tolist()

    for i in range(idx, len(times)):
        accel_time = times[i]

        while rot_time < accel_time:
            if rot_idx == len(rot_t):
                break
            rot_time = rot_t[rot_idx]
            rot = rot_dat[rot_idx]
            rot_idx += 1
            
        pose = so3.from_quaternion((rot[3], *rot[0:3]))

        accel = accels[i, :]
        dt = times[i] - times[i-1]
        v += accel * dt
        if vo.norm(v) < 0.1:
            v *= 0.9
        v_buf.add_data([times[i], *v])
        pose_buf.add_data([times[i], *pose])
        timestep += 1

    latest = times[-1]

    #plt.clf()
    dat = v_buf.get_data()
    #plot = rpyc.async_(plt.plot)
    #plot(dat[:, 0], dat[:, 1], label="x")
    #plot(dat[:, 0], dat[:, 2], label="y")
    #plot(dat[:, 0], dat[:, 3], label="z")
    #plt.plot(dat[:, 0], dat[:, 1], label="x")
    #plt.plot(dat[:, 0], dat[:, 2], label="y")
    #plt.plot(dat[:, 0], dat[:, 3], label="z")
    #plt.legend()
    #time.sleep(0.05)
    #print(raw_accel)
    print(pose)
    print(timestep)

#plt.stop()
