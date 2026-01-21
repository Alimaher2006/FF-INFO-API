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

# بيانات الاتصال
key = "Yg&tc%DEuh6%Zc^8"
iv = "6oyZDr22E3ychjM%"

def get_jwt_from_remote():
    try:
        url = "https://ff-jwt-alis-projects-afe2993a.vercel.app/token?uid=3996382218&password=1FD175170B35C52093D16569160DBC46FB2C071F24429AE7BCBE04A596AB8350"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print("Failed to get JWT:", response.text)
            return None
    except Exception as e:
        print("Error fetching JWT:", str(e))
        return None

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

def get_headers():
    token = get_jwt_from_remote()
    if not token:
        raise Exception("فشل في الحصول على التوكن من الموقع الخارجي")
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; ASUS_Z01QD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",
        "X-Unity-Version": "2018.4.11f1",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "ReleaseVersion": "OB52",
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
    headers = get_headers()
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
        result['Owners'] = ['Ali Maher 🌸']
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


