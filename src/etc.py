import portalocker, json, time, os, re

usersFile = "data/users.json"
chainFile = "data/chain.json"
centralServersFile = "data/centralServers.json"
secretKeyFile = "data/secretKey.json"

def saveData(filename, data):
    try:
        with open(filename, "w") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            json.dump(data, f)
            time.sleep(2)
            portalocker.unlock(f)
    except:
        pass

def loadData(filename, empty=[]):
    # 初期化？
    if "data" in locals(): del data
    try:
        with open(filename, "r") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            data = json.load(f)
            time.sleep(2)
            portalocker.unlock(f)
    except:
        data = empty
    return data

def addUniqueElements(a1, a2, url=False):
    result = a1
    for i in a2:
        if url and i[-1] == "/": i = i.rstrip("/")
        if not i in result:
            result.append(i)
    return result

def addUniqueKeys(d1 : dict, d2 : dict):
    # 辞書の足し算
    result = dict(d1)
    for key, value in d2.items():
        if not key in result:
            result[key] = value
    return result

def extractBaseUrl(text):
    # URLを見つけるための正規表現パターン
    urlPattern = r'https?://[^\s]+'
    # 最初のURLを見つける
    match = re.search(urlPattern, text)
    if match:
        # 完全なURLを取得
        fullUrl = match.group(0)
        # プロトコルとドメイン部分を抽出するための正規表現パターン
        baseUrlPattern = r'https?://[^/]+'
        baseUrlMatch = re.search(baseUrlPattern, fullUrl)
        if baseUrlMatch:
            return baseUrlMatch.group(0)
    return None

users = loadData(usersFile, empty={})
centralServers = loadData(centralServersFile)
if os.path.isfile("BOOTSTRAPSERVER"):
    with open("BOOTSTRAPSERVER") as f:
        centralServers.append(f.read())
if centralServers == []:
    try:
        centralServers.append(input("初期中央サーバー(例: http://xxx.com:11380): "))
        with open("BOOTSTRAPSERVER", mode="w") as f:
            f.write(centralServers[0])
        saveData(centralServersFile, centralServers)
    except EOFError:
        # Systemdとかで実行したときに落ちないように
        pass