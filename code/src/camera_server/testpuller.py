import requests

rsp = requests.get(url = "http://10.192.173.150:5000/pose")

jason = rsp.json()

pose = jason['pose']
time = jason['time']

print(pose)
print(time)
