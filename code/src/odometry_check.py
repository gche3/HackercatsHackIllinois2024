import json
import phone_sensors

import numpy as np
from klampt.math import vectorops as vo, so3, se3
import matplotlib.pyplot as plt

powers = [0.7, 0.8, 0.9, 1]

log_data = [json.loads(x) for x in open("linear.log").readlines()]
#log_data = [json.loads(x) for x in open("rotate.log").readlines()]
i = 0

def vel_model(power, v_prev, dt):
    K1 = 1.5/3
    K2 = 1
    K3 = K1 * 0.7 - 0.15
    dvdt = (K1 * power - v_prev)
    if v_prev > 0:
        dvdt = max(0, dvdt - K3)
    elif v_prev < 0:
        dvdt = min(0, dvdt + K3)
    else:
        if dvdt > 0:
            dvdt = max(0, dvdt - K3)
        else:
            dvdt = min(0, dvdt + K3)
    return v_prev + K2 * dvdt * dt

def omega_model(power, v_prev, dt):
    K1 = 5.2
    K2 = 4
    K3 = K1 * 0.6 / 4
    dvdt = (K1 * power - v_prev)
    if v_prev > 0:
        dvdt = max(0, dvdt - K3)
    elif v_prev < 0:
        dvdt = min(0, dvdt + K3)
    else:
        if dvdt > 0:
            dvdt = max(0, dvdt - K3)
        else:
            dvdt = min(0, dvdt + K3)
    return v_prev + K2 * dvdt * dt

for power in powers:
    log = log_data[i]
    while abs(log['cmd_vel'][0]) != power:
        i += 1
        log = log_data[i]

    sensors = phone_sensors.break_log(log_data[i-1]['imu'])
    t0 = log['time']
    prev_t = 0
    v = np.zeros(3)

    accels = []
    vels = []
    vel_pred = [0]
    ts = []
    thetas = []
    omegas = []
    omega_preds = [0]
    pose = so3.identity()
    theta = 0
    while abs(log['cmd_vel'][0]) == power:
        sensors = phone_sensors.break_log(log['imu'])
        t = log['time'] - t0

        dt = t - prev_t
        prev_t = t

        rot = sensors['rot']
        accel = sensors['accel']
        accel[2] *= -1

        drot = so3.from_rotation_vector(vo.mul(rot, dt))
        pose = so3.mul(drot, pose)
        theta += rot[2] * dt
        thetas.append(theta)
        omegas.append(rot[2])
        omega_preds.append(omega_model(power, omega_preds[-1], dt))

        #accel = np.array(so3.apply(pose, accel))
        accel = np.array(accel)

        vel_pred.append(vel_model(-power, vel_pred[-1], dt))
        v += accel * dt

        accels.append(accel)
        vels.append(v.tolist())
        ts.append(t)

        i += 1
        log = log_data[i]

    for j in range(50):
        sensors = phone_sensors.break_log(log['imu'])
        t = log['time'] - t0

        dt = t - prev_t
        prev_t = t

        rot = sensors['rot']
        accel = sensors['accel']
        accel[2] *= -1

        drot = so3.from_rotation_vector(vo.mul(rot, dt))
        pose = so3.mul(drot, pose)
        theta += rot[2] * dt
        thetas.append(theta)
        omegas.append(rot[2])
        omega_preds.append(omega_model(power, omega_preds[-1], dt))

        #accel = np.array(so3.apply(pose, accel))
        accel = np.array(accel)

        vel_pred.append(vel_model(-power, vel_pred[-1], dt))
        v += accel * dt

        accels.append(accel)
        vels.append(v.tolist())
        ts.append(t)

        i += 1
        log = log_data[i]
    
    plt.figure()
    vels = np.array(vels)
    #plt.plot(ts, vels[:, 0], label='vx')
    plt.plot(ts, vels[:, 1], label='v_meas')
    plt.plot(ts, vel_pred[1:], label='v_pred')
    #plt.plot(ts, vels[:, 2], label='vz')
    #plt.plot(ts, accels, label='a')
    #plt.plot(ts, thetas, label='theta')
    #plt.plot(ts, omegas, label='w')
    #plt.plot(ts, omega_preds[1:], label='w_pred')
    plt.title(f"power={power}")
    plt.legend()
    plt.show()

    #input()

