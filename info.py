from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import requests
from flask import Flask, jsonify, request
from data_pb2 import AccountPersonalShowInfo
from google.protobuf.json_format import MessageToDict
import uid_generator_pb2
import threading

app = Flask(__name__)

# التوكن تحطه هنا يدويًا
jwt_token = "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxMjQ3MzUyNzgzMSwibmlja25hbWUiOiJBbGltYWhlcl8wMDIiLCJub3RpX3JlZ2lvbiI6Ik1FIiwibG9ja19yZWdpb24iOiJNRSIsImV4dGVybmFsX2lkIjoiOWRmZTYzZjhkZTk4ODY4NjExNTM3MmM3MTdhNTU5MjIiLCJleHRlcm5hbF90eXBlIjo0LCJwbGF0X2lkIjoxLCJjbGllbnRfdmVyc2lvbiI6IjEuMTA4LjMiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiRlIiLCJleHRlcm5hbF91aWQiOjM5OTYzODIyMTgsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjo0LCJsb2NrX3JlZ2lvbl90aW1lIjoxNzUwODY4NTQzLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6IiIsInVzaW5nX3ZlcnNpb24iOjEsInJlbGVhc2VfY2hhbm5lbCI6IjNyZF9wYXJ0eSIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTEiLCJleHAiOjE3NjgxNDMzNjB9.txJtgj70iZGp9Ckkf36aDEaZoCr0Sb3e67Xw7OUthOU"

# بيانات الاتصال
key = "Yg&tc%DEuh6%Zc^8"
iv = "6oyZDr22E3ychjM%"

def get_api_endpoint(region):
    endpoints = {
        "IND": "https://client.ind.freefiremobile.com/GetPlayerPersonalShow",
        "BR": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "US": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "SAC": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "NA": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
        "default": "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    }
    return endpoints.get(region, endpoints["default"])

def get_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; ASUS_Z01QD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",
        "X-Unity-Version": "2018.4.11f1",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "ReleaseVersion": "OB50",
        "X-GA": "v1 1",
        "X-Requested-With": "com.dts.freefireth"
    }

def encrypt_aes(hex_data, key, iv):
    key = key.encode()[:16]
    iv = iv.encode()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(bytes.fromhex(hex_data), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return binascii.hexlify(encrypted_data).decode()

def apis(idd, region):
    endpoint = get_api_endpoint(region)    
    headers = get_headers(jwt_token)
    try:
        data = bytes.fromhex(idd)
        response = requests.post(
            endpoint,
            headers=headers,
            data=data,
            timeout=10
        )
        response.raise_for_status()
        return response.content.hex()
    except requests.exceptions.RequestException as e:
        print(f"API request to {endpoint} failed: {e}")
        raise

@app.route('/accinfo', methods=['GET'])
def get_player_info():
    try:
        uid = request.args.get('uid')
        region = request.args.get('region', 'default').upper()
        custom_key = request.args.get('key', key)
        custom_iv = request.args.get('iv', iv)
        if not uid:
            return jsonify({"error": "UID parameter is required"}), 400

        message = uid_generator_pb2.uid_generator()
        message.saturn_ = int(uid)
        message.garena = 1
        protobuf_data = message.SerializeToString()
        hex_data = binascii.hexlify(protobuf_data).decode()
        encrypted_hex = encrypt_aes(hex_data, custom_key, custom_iv)
        api_response = apis(encrypted_hex, region)
        if not api_response:
            return jsonify({"error": "Empty response from API"}), 400
        message = AccountPersonalShowInfo()
        message.ParseFromString(bytes.fromhex(api_response)) 
        result = MessageToDict(message)
        result['Owners'] = ['TeamxCutehack!!']
        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid UID format"}), 400
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": f"Failure to process the data: {str(e)}"}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5552)
