from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from etc import *
from blockchain import BlockChain
import traceback, requests

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["10000 per day", "3000 per hour"]
)

chain = []

blockchain = BlockChain()

@app.route("/", methods=["GET"])
def index():
    return jsonify({"hello": "world"}), 200

@app.route("/getCentralServers", methods=["GET"])
def getCentralServers():
    return jsonify({"centralServers": loadData(centralServers)}), 200

@app.route("/sync", methods=["POST"])
def sync():
    global blockchain, users
    syncData = request.json

    chain = syncData["chain"]
    rtc = tc = 0
    result = {"chain": blockchain.chain, "users": users, "centralServers": centralServers}
    for c in chain:
        for t in range(len(c["transactions"])):
            rtc += 1
    for c in blockchain.chain:
        for t in range(len(c["transactions"])):
            tc += 1
    if rtc > tc:
        blockchain.chain = chain
        saveData(chainFile, blockchain.chain)
    users = addUniqueKeys(users, syncData["users"])
    saveData(usersFile, users)
    return jsonify(result), 200

@app.route("/registerCentralServer", methods=["GET"])
def registerCentralServer():
    global centralServers
    try:
        response = requests.get(f"http://{request.remote_addr}:11380/", timeout=7)
        if response.status_code == 200 and "hello" in response.json():
            if response.json()["hello"] == "world":
                centralServers = addUniqueElements(centralServers, [f"http://{request.remote_addr}:11380"])
                saveData(centralServersFile, centralServers)
                return jsonify({"result": 0}), 200
        print({"result": 2})
        return jsonify({"result": 2}), 500
    except:
        print(traceback.format_exc())
        return jsonify({"result": 1}), 500

def reigsterSelfCentralServer():
    global centralServers
    connect = False
    for centralServer in centralServers:
        try:
            response = requests.get(f"{centralServer}/registerCentralServer", timeout=7)
            result = response.json()["result"]
            if result == 0:
                connect = True
                print(f"登録: サーバー: {centralServer}")
            elif result == 1:
                print(f"エラー: 不明\nサーバー: {centralServer}")
            elif result == 2:
                print(f"エラー: このサーバーは相手のサーバーと合いません\nサーバー: {centralServer}")
        except requests.exceptions.RequestException as e:
            print(f"エラー: 中央サーバーに接続できません\nサーバー: {centralServer}")
            centralServers.remove(centralServer)
        except:
            if not extractBaseUrl(centralServer): centralServers.remove(centralServer)
        saveData(centralServersFile, centralServers)
    if not connect:
        print("エラー: どの中央サーバーにも接続できませんでした。\ndata/centralServers.jsonを削除し、初期ノードを設定してください")

def syncPeriodically():
    # 定期同期のための関数
    global centralServers
    print("定期的な同期")
    while True:
        time.sleep(5)
        reigsterSelfCentralServer()
        connect = False
        centralServers = list(set(centralServers))
        print(f"中央サーバー:{centralServers}")
        for centralServer in centralServers:
            try:
                response = requests.get(f"{centralServer}/getCentralServers", timeout=7)
                responseCentralServers = []
                for responseCentralServer in response.json()['centralServers']:
                    if extractBaseUrl(responseCentralServer):
                        responseCentralServers.append(extractBaseUrl(responseCentralServer))
                centralServers = addUniqueElements(centralServers, responseCentralServers, url=True)
                connect = True
            except requests.exceptions.RequestException as e:
                centralServers.remove(centralServer)
            except Exception as e:
                print(e)
                if not extractBaseUrl(centralServer): centralServers.remove(centralServer)
        saveData(centralServersFile, centralServers)
        if not connect:
            print("エラー: どの中央サーバーにも接続できませんでした。\ndata/centralServers.jsonを削除し、初期ノードを設定してください")