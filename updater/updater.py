import os
from dotenv import load_dotenv
from web3 import Web3
import requests
import time
from datetime import datetime

web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/cdd85a80d6594d22b237d1c12ba9aef8'))
load_dotenv()

site = "http://localhost:8000"

def getFloorPrice(collection_slug):
    response = requests.get(
        f'https://api.opensea.io/collection/{collection_slug}')
        
    return response.json()['collection']['stats']['floor_price']

def getNFTInfo(contract_address):
    checksum_contract_address = web3.toChecksumAddress(contract_address)
    response = requests.get(
        f'https://api.opensea.io/asset_contract/{checksum_contract_address}')
    collection = response.json()['collection']['slug']
    floor_price = getFloorPrice(collection)
    return checksum_contract_address, collection, floor_price

def login():
    url = f"{site}/login"
    payload={'username': os.getenv('AUTH_AC'),
    'password': os.getenv('AUTH_PW')}
    files=[

    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    # if response.json()['access_token']:
    #     print("Login Success...")
    return response.json()

def getIndexList(access_token, token_type):
    url = f"{site}/component/all"
    payload={}
    headers = {
    'Authorization': str(token_type+' '+access_token)
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    # if (len(response.json())):
    #     print("getIndexList Success...")
    return response.json()

def checkAuth(auth):
    newAuth = login()
    print(newAuth['access_token'])
    print(auth['access_token'])
    if newAuth['access_token'] != auth['access_token']:
        auth['access_token'] = newAuth['access_token']
    else:
        print('Same Token')

def initLocalData():
    local_data = {}
    db_data = {}
    local_auth = login()
    component_raw = getIndexList(local_auth['access_token'],local_auth['token_type'])


    # collections
    local_data['collections'] = {}

    for i,component in enumerate(component_raw):
        local_data['collections'][i]={}
        local_data['collections'][i]['collection_name']=component['collection']
        local_data['collections'][i]['contract_address']=component['contract_address']
        local_data['collections'][i]['floor_price']=component['floor_price']
        local_data['collections'][i]['weighting']=component['weighting']
        local_data['collections'][i]['last_update_timestamp']=component['last_update_timestamp']
    return local_data, local_auth

def updateComponents(local_data):
    for i in local_data['collections']:
        # update
        try:
            floor_price = getFloorPrice(local_data['collections'][i]['collection_name'])
            if floor_price > 0:
                local_data['collections'][i]['floor_price'] =  floor_price 
                local_data['collections'][i]['last_update_timestamp'] = int(datetime.now().timestamp())
                #print(f"Updated {local_data['collections'][i]['collection_name']} with FP {local_data['collections'][i]['floor_price']} at {local_data['collections'][i]['last_update_timestamp']}...")
        except Exception as e: 
            print(e)
        time.sleep(1)
        # print(index)
    return local_data
        
def feedDictConstructor(local_data):
    db_data = {}
    # blocktime
    db_data['block_number'] = web3.eth.block_number
    # timestamp
    db_data['current_timestamp'] = int(datetime.now().timestamp())
    # avg_delay
    delay = 0
    index = 0
    for i in (local_data['collections']):
        index += local_data['collections'][i]['floor_price'] * local_data['collections'][i]['weighting']
        delay += int(datetime.now().timestamp())-local_data['collections'][i]['last_update_timestamp']
    db_data['avg_delay'] = delay /(i+1)
    db_data['index'] =index
    return db_data
    
def appendDB(auth,db_data):
    headers = {
        'accept': 'application/json',
        'Authorization': f"{auth['token_type']} {auth['access_token']}",
        # Already added when you pass json= but not when you pass data=
        # 'Content-Type': 'application/json',
    }

    json_data = {
        'index': db_data['index'],
        'timestamp': db_data['current_timestamp'],
        'blocktime': db_data['block_number'],
        'avg_delay': db_data['avg_delay']
    }
    response = requests.post(f"{site}/history/add", headers=headers, json=json_data)
   
if __name__ == '__main__':
    local_data, auth = initLocalData()
    epoch = 0
    while True:
        try:
            auth = login()
            updateComponents(local_data)
            db_data = feedDictConstructor(local_data)
            appendDB(auth,db_data)
            epoch+=1
            print(f"Epoch: {epoch} Last update timestamp: {int(datetime.now().timestamp())} NFT Index: {db_data['index']}")
        except Exception as e:
            print(e)
            auth = login()