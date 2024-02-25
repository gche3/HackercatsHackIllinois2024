
import requests

SERVER_URL = "http://10.192.173.150:5000"
def server_get(endpoint):
    return requests.get(SERVER_URL+endpoint).json()
