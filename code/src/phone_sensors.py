import requests
from threading import Thread
import time

import numpy as np
import numpy.linalg as la
from klampt.math import vectorops as vo, so3, se3

try:
    from src.utils.plot_ringbuffer import ArrayRingBuffer
    from src.utils.math import *
except ImportError:
    from utils.plot_ringbuffer import ArrayRingBuffer
    from utils.math import *

def break_log(array):
    return {
        "rot": array[0],
        "accel": array[1],
    }

PP_CHANNELS = ["gyrX", "linZ"]

class PhoneSensors:
    
    def __init__(self, address, port="8081"):
        self.address = address
        self.port = port
        self._data = np.zeros(2)    # temp buffer, synced to self.data on loop
        self.data = np.zeros(2)

        # integrated only velocity
        self.v_est = 0
        self.power = 0
        self.pose = np.zeros(3)
        self.x = np.zeros(2)
        self.P = np.array([1.0, 1.0])
        self.theta = 0
        self.loop_thread = None
        self.started = False
        self.prev_t = None
    
    def sync(self, power):
        self.power = power
        self.data = self._data

    def startup(self):
        def loop_func():
            self.started = True
            self.prev_t = time.monotonic()
            self._loop(None)
            while self.started:
                self._loop(time.monotonic())
                time.sleep(0.01)
        self.loop_thread = Thread(group=None, target=loop_func, name="phone_sensors:loop")
        self.loop_thread.start()
        while not self.started:
            time.sleep(1)

    def shutdown(self):
        self.started = False
        self.loop_thread.join()
        self.loop_thread = None

    def _loop(self, t):
        req = requests.get(f"http://{self.address}:{self.port}/get?"+("&".join(PP_CHANNELS)))
        x = req.json()['buffer']
        if t is None:
            return

        data = np.zeros(2)
        for i, k in enumerate(PP_CHANNELS):
            data[i] = x[k]['buffer'][0]
        data[1] *= -1
        self._data = data.copy()

        dt = t - self.prev_t
        self.prev_t = t

        self.v_est += data[1] * dt
        self.theta += data[0] * dt

        self.kalman_filter(dt)
        self.pose += np.array(self.get_vel()) * dt

    def kalman_filter(self, dt):
        F = np.array([[1, -dt], [0, 1]])
        B = np.array([[dt], [0]])
        H = np.array([[1, 0]])
        Q = np.array([[0.5, 0], [0, 0.0001]])
        R = 0.001
        
        xhat = F @ self.x.reshape(-1, 1) + B * self.v_est
        Phat = F @ self.P @ F.T + Q

        def vel_model(power, v_prev, dt):
            K1 = 1.5/3
            K2 = 1
            K3 = K1 * 0.7 - 0.15
            dvdt = (K1 * power - v_prev)
            if v_prev > 0:
                if dvdt > 0:
                    dv = K2 * max(0, dvdt - K3) * dt
                else:
                    dv = (dvdt-min(K3, v_prev)) * dt
            elif v_prev < 0:
                if dvdt < 0:
                    dv = K2 * min(0, dvdt + K3) * dt
                else:
                    dv = (dvdt+min(K3, -v_prev)) * dt
            else:
                if dvdt > 0:
                    dv = K2 * max(0, dvdt - K3) * dt
                else:
                    dv = K2 * min(0, dvdt + K3) * dt
            return v_prev + dv

        z = vel_model(self.power, self.x[0], dt)
        y = z - H @ xhat
        #y = z - xhat[0]
        S = H @ Phat @ H.T + R
        K = Phat @ H.T * (1/S)

        self.x = (xhat + K * y)[:, 0]
        self.P = (np.eye(2) - K @ H) @ Phat

    def get_latest_data(self):
        if self.data is None:
            return None
        return self.data.tolist()

    def get_vel(self):
        ret = [self.x[0] * np.cos(self.theta), self.x[0] * np.sin(self.theta), self.data[0]]
        return ret
