import traceback, requests, datetime, hashlib, secrets, jwt, os
from etc import *
from flask import Flask, request, make_response, redirect, url_for, session, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from blockchain import BlockChain

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10000 per day", "3000 per hour"]
)

secretKey = loadData(secretKeyFile, empty={})
if not "key" in secretKey:
    secretKey["key"] = secrets.token_hex(16)
    saveData(secretKeyFile, secretKey)
app.secret_key = secretKey["key"]

blockchain = BlockChain()

def generateToken(username, password):
    # JWTトークン（ログイントークン）生成関数
    token = jwt.encode({
        "username": username,
        "password": password, 
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=48)
    }, app.secret_key, algorithm="HS256")
    return token

def authenticate(username, password):
    # ユーザー認証関数
    if (hashlib.sha256(username.encode()).hexdigest()
    in users and users[hashlib.sha256(username.encode()).hexdigest()]["password"]
    == hashlib.sha256(password.encode()).hexdigest()):
        return True
    return False

@app.route("/register", methods=["GET", "POST"])
def register():
    # ユーザー登録エンドポイント
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if authenticate(username, password):
            return render_template("register.html", error="登録に失敗しました\n既に登録されています")
        
        # ユーザー名のハッシュ（アドレス）で保存
        address = hashlib.sha256(username.encode()).hexdigest()
        hashedPassword = hashlib.sha256(password.encode()).hexdigest()
        users[address] = {
            'password': hashedPassword,
            'balance': 0  # 初期残高を0に設定
        }
        saveData(usersFile, users)
        
        # indexに移動するために認証しておく
        if authenticate(username, password):
            response = make_response(redirect(url_for("index")))
            token = generateToken(username, password)
            response.set_cookie("token", token)
            return response
        return redirect(url_for("login"))
    return render_template("register.html")

def requiresAuth(f):
    # 認証が必要なエンドポイント用のデコレータ
    global session
    @wraps(f)
    def decorated(*args, **kwargs):
        # トークンを取得
        token = request.cookies.get("token")
        if not token:
            # トークンを持ってないのなら
            return redirect(url_for("login"))
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            if authenticate(data["username"], data["password"]):
                session["username"] = data["username"]
            else:
                session["username"] = None
                return redirect(url_for("login"))
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login"))
        except jwt.InvalidTokenError:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    # ログインエンドポイント
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if authenticate(username, password):
            token = generateToken(username, password)
            response = make_response(redirect(url_for("index")))
            # トークンをクッキーに保存
            response.set_cookie("token", token)
            return response
        else:
            return render_template("login.html", error="ログインに失敗しました")
    return render_template("login.html")

@app.route("/logout")
@requiresAuth
def logout():
    # ログアウトエンドポイント
    response = make_response(redirect(url_for("login")))
    # トークンを削除（ログアウト）
    response.delete_cookie("token")
    return response

@app.route('/')
@requiresAuth
def index():
    username = session['username']
    address = hashlib.sha256(username.encode()).hexdigest()
    balance = blockchain.getBalance(address)
    return render_template('index.html', username=username, address=address, balance=balance)

@app.route("/yourTransactions")
def yourTransactions():
    username = session['username']
    address = hashlib.sha256(username.encode()).hexdigest()
    return render_template("yourTransactions.html", chain=blockchain.chain, address=address)

@app.route("/mine", methods=["GET"])
@requiresAuth
def mine():
    if os.path.isfile("DONTMINING"):
        return render_template("cantMining.html")
    address = hashlib.sha256(session["username"].encode()).hexdigest()
    block = blockchain.newTransaction(recipient=address)[1]
    balance = blockchain.getBalance(address)
    return render_template("mine.html", block=block, balance=balance)

@app.route('/chain', methods=['GET'])
def fullChain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/users', methods=['GET'])
def getUsers():
    return jsonify(users)

def sync():
    # データ同期
    global centralServers, blockchain, users
    data = {
        'chain': blockchain.chain,
        'users': users
    }
    longestChain = None
    connect = False
    message = ""
    centralServers = list(set(centralServers))
    print(f"中央サーバー:{centralServers}")
    for centralServer in centralServers:
        try:
            # データを送信
            response = requests.post(f"{centralServer}/sync", data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=7)
            if response.status_code == 200:
                chain = response.json()['chain']
                users = addUniqueKeys(users, response.json()['users'])
                okChain = blockchain.validChain(chain)
                # transaction count var
                rtc = tc = 0
                for c in okChain:
                    for _ in range(len(c["transactions"])):
                        rtc += 1
                for c in blockchain.chain:
                    for _ in range(len(c["transactions"])):
                        tc += 1
                print(tc, rtc)
                if rtc > tc:
                    # 取得したチェーンのトランザクション数が
                    # 今のトランザクション数より大きかった時
                    blockchain.chain = longestChain = okChain
                responseCentralServers = []
                for responseCentralServer in response.json()['centralServers']:
                    if extractBaseUrl(responseCentralServer):
                        responseCentralServers.append(extractBaseUrl(responseCentralServer))
                centralServers = addUniqueElements(centralServers, responseCentralServers, url=True)
                connect = True
            else:
                message += f"エラー: エラーレスポンスが返されました サーバー:{centralServer}<br/>\n"
        except requests.exceptions.RequestException as e:
            message += f"接続エラー: {e} サーバー:{centralServer}<br/>\n"
            centralServers.remove(centralServer)
        except Exception as e:
            print(traceback.format_exc())
            message += f"エラー: {e} サーバー:{centralServer}<br/>\n"
            if not extractBaseUrl(centralServer): centralServers.remove(centralServer)
    saveData(centralServersFile, centralServers)
    if not connect:
        message += "エラー: どの中央サーバーにも接続できませんでした。<br/>\nサーバー管理者はdata/centralServers.jsonを削除し、初期ノードを設定してください<br/>\n"
    if longestChain:
        blockchain.chain = longestChain
        saveData(chainFile, blockchain.chain)
        message += 'ブロックチェーンが同期されました'
    else:
        message += '既存のブロックチェーンが最長です'
    print(message.replace("<br/>", ""))
    saveData(usersFile, users)
    return message

@app.route("/send", methods=["GET", "POST"])
@requiresAuth
def send(sender, recipient, amount):
    # 送金
    if request.method == "POST":
        # 一応ちゃんとほかのノードにこの人の履歴がないか同期しとく
        if amount < 0.001:
            return False, "送金額は0.001より小さくできません"
        sync()
        if blockchain.getBalance(sender) < amount:
            return False, "残高が不足しています"
        elif blockchain.newTransaction(sender, recipient, amount) == 114514:
            return False, "送金時のプルーフ計算に失敗しました"
        blockchain.newTransaction(sender, recipient, amount)
        return True, "送金が成功しました"
    return render_template("send.html")

@app.route("/send", methods=["GET", "POST"])
def sendPage():
    result, message = send(hashlib.sha256(session["username"].encode()).hexdigest(), request.form["recipient"], float(request.form["amount"]))
    if result:
        return render_template("send.html", success=message)
    else:
        return render_template("send.html", error=message)

@app.route("/sendUrl", methods=["GET"])
@requiresAuth
def sendFromUrlPage():
    result, message = send(hashlib.sha256(session["username"].encode()).hexdigest(), request.args.get("recipient"), float(request.args.get("amount")))
    if result:
        return render_template("send.html", success=message)
    else:
        return render_template("send.html", error=message)

@app.route('/sync', methods=['GET'])
def syncPage():
    if os.path.isfile("DONTMANUALSYNC"):
        return render_template("cantManualSync.html")
    return render_template('sync.html', message=sync())

def syncPeriodically():
    # 定期同期のための関数
    time.sleep(5)
    while True:
        print("定期的な同期")
        sync()
        time.sleep(10)