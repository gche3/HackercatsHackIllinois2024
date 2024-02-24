import requests

from utils.plot_ringbuffer import ArrayRingBuffer
from utils.math import *

class PhoneSensors:
    
    def __init__(self, address):
        self.address = address
        self.data_buffer = np
        # time, raw: accel, gravity, rotvec
        self.data_buffer = ArrayRingBuffer(20, 1+3+3+4)
        self.timestep = 0
        self.latest_sensor_time = -1

    def loop(self):
        x = requests.get(f"http://{self.address}/sensors.json").json()
        _accels = x['accel']['data']
        _gravs = x['gravity']['data']
        _rots = x['rot_vector']['data']

        times = np.array([dat for dat, _ in _accels]) / 1000
        accels = np.array([dat for _, dat in _accels])

        grav_t = np.array([dat for dat, _ in _gravs]) / 1000
        grav_dat = np.array([dat for _, dat in _gravs])
        rot_t = np.array([dat for dat, _ in _rots]) / 1000
        rot_dat = np.array([dat for _, dat in _rots])

        # We want to be right handed
        accels[:, 2] *= -1
        grav_dat[:, 2] *= -1

        # The index of the next reading to integrate.
        # might equal length of array if there's no more readings to integrate.
        idx = np.searchsorted(times, self.latest_sensor_time)+1
        grav_idx = np.searchsorted(grav_t, self.latest_sensor_time)
        rot_idx = np.searchsorted(rot_t, self.latest_sensor_time)

        grav_time = grav_t[grav_idx]
        grav_idx += 1
        rot_time = rot_t[rot_idx]
        rot_idx += 1

        # Synchronize to the acceleration buffer.
        for i in range(idx, len(times)):
            accel_time = times[i]

            while grav_time < accel_time:
                if grav_idx == len(grav_t):
                    break
                grav_time = grav_t[grav_idx]
                grav_idx += 1
            while rot_time < accel_time:
                if rot_idx == len(rot_t):
                    break
                rot_time = rot_t[rot_idx]
                rot_idx += 1
                
            self.timestep += 1
        grav = in
        self.latest_sensor_time = times[-1]

