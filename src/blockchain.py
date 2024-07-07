import datetime, hashlib, json
from decimal import Decimal
from etc import *

class BlockChain:
    def __init__(self, miningDifficulty = 6):
        # チェーンデータの読み込み
        self.chain = loadData(chainFile)
        self.transactions = []
        self.difficulty = miningDifficulty # 難易度を設定
        if not self.chain:
            self.newBlock(100, previousHash='1')
    
    def newBlock(self, proof, previousHash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'transactions': self.transactions,
            'proof': proof,
            'previousHash': previousHash or self.hash(self.chain[-1]),
        }

        # 現在のトランザクションリストをリセット（ファイルに保存）
        self.transactions = [] 
        self.chain.append(block)
        # チェーンデータを保存
        saveData(chainFile, self.chain)
        return block
    
    def mining(self, address, newBlock=True):
        lastBlock = self.lastBlock
        lastProof = lastBlock["proof"]
        proof = self.proofOfWork(lastProof)
        self.transactions.append({
            "sender": "0",
            "recipient": address,
            "amount": 0.001,
        })
        previousHash = self.hash(lastBlock)
        block = self.chain[-1]
        
        if newBlock:
            block = self.newBlock(proof, previousHash)
        return block
    
    def newTransaction(self, sender=None, recipient="", amount=None):
        # 新しいトランザクションを作成してトランザクションリストに追加
        if not None in [sender, amount]:  
            self.transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
            lastBlock = self.lastBlock
            proof = self.proofOfWork(lastBlock["proof"])
            previousHash = self.hash(lastBlock)
            self.newBlock(proof, previousHash)
        currentTime = datetime.datetime.now()
        blockCreateTime = datetime.datetime.strptime(self.lastBlock["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
        if blockCreateTime > currentTime - datetime.timedelta(minutes=10) and self.chain[-1]["index"] != 1:
            # 最後のブロックが作られた時間と今の時間が10分以内なら
            # 最後のブロックのトランザクション配列にappendする。
            self.mining(recipient, newBlock=False)
            self.chain[-1]["transactions"].append(self.transactions[-1])
            block = self.chain[-1]
            saveData(chainFile, self.chain)
            print(self.transactions[-1])
        else:
            block = self.mining(recipient)
            print("新しいブロック", block)
        return self.lastBlock['index'] + 1, block
    
    @staticmethod
    def hash(block):
        # ブロックのハッシュ値を計算する
        blockString = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(blockString).hexdigest()
    
    @property
    def lastBlock(self):
        # 最後のブロックを返す
        return self.chain[-1]

    def proofOfWork(self, lastProof):
        # ブロックチェーンの新しいブロックを生成するための証明
        proof = 0
        while not self.validProof(lastProof, proof):
            proof += 1
        return proof

    def validProof(self, lastProof, proof):
        # ハッシュが正しいか判別
        guess = f'{lastProof}{proof}'.encode()
        guessHash = hashlib.sha256(guess).hexdigest()
        return guessHash[:self.difficulty] == "0" * self.difficulty
    
    def getBalance(self, address):
        # 所持金表示
        balance = Decimal(0)
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['sender'] == address:
                    balance -= Decimal(str(transaction['amount']))
                if transaction['recipient'] == address:
                    balance += Decimal(str(transaction['amount']))
        return balance
    
    def validChain(self, chain):
        # チェーンが有効かどうかを確認する
        bootstrapChain = {"chain":[{"index": 1, "previousHash": "1", "proof": 100, "timestamp": "2024-06-20 09:45:31.766780", "transactions": []}], "length": 1}
        okChain = chain
        for i in range(1, len(chain)):
            currentBlock = chain[i]
            previousBlock = chain[i - 1]
            if currentBlock["previousHash"] != self.hash(previousBlock):
                print(f"Block {i} has incorrect previous hash.\n{currentBlock['previousHash']}!={self.hash(previousBlock)}")
                return bootstrapChain
            elif not self.validProof(previousBlock["proof"], currentBlock["proof"]):
                print(f"Block {i} has invaild proof of work.")
                return bootstrapChain
            if currentBlock['proof'] == None:
                print(f"警告:このブロック({i})のproofはnullです")
            for j in reversed(range(len(currentBlock["transactions"]))):
                if currentBlock["transactions"][j]["sender"] == "0" and not currentBlock["transactions"][j]["amount"] <= 0.001:
                    okChain[i]["transactions"].pop(j)
                elif not currentBlock["transactions"][j]["sender"] == "0" and currentBlock["transactions"][j]["amount"] < 0.001:
                    okChain[i]["transactions"].pop(j)
        return okChain