import os
from dotenv import load_dotenv
from web3 import Web3
import requests
import time
from datetime import date, datetime

web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/cdd85a80d6594d22b237d1c12ba9aef8'))
load_dotenv()

def login():
    url = "http://13.235.247.150/login"
    payload={'username': os.getenv('AUTH_AC'),
    'password': os.getenv('AUTH_PW')}
    files=[

    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    # if response.json()['access_token']:
    #     print("Login Success...")
    return response.json()

def appendDB(auth):
    headers = {
        'accept': 'application/json',
        'Authorization': f"{auth['token_type']} {auth['access_token']}",
        # Already added when you pass json= but not when you pass data=
        # 'Content-Type': 'application/json',
    }

    json_data = {
    }
    response = requests.post('http://13.235.247.150/history/add', headers=headers, json=json_data)
   
if __name__ == '__main__':
    epoch = 0
    while True:
        try:
            auth = login()
            appendDB(auth)
            time.sleep(10)
            epoch+=1
            print(f"Epoch: {epoch} Last update timestamp: {int(datetime.now().timestamp())}")
        except Exception as e:
            print(e)
            auth = login()