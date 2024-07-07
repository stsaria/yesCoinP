# YesCoin
![YesCoin Logo](src/static/logo.png "YesCoin Logo")
このリポジトリにアクセスしていただいて、お誠にありがとうございます！
## YesCoinとは
YesCoinはある団体(YINST)の、仮想通貨です。
ビットコインのように良い作りはしていませんが、
この仮想通貨が広まるとうれしいです！

お願い：YesCoinはできたばかりでバグが多いので、アップデートが頻繁に起こります

定期的に```git pull```をしていただけると助かります
## 動作要件
- Python3(~3.9ぐらいがおすすめ)
- pip3
- git
## 使用ポート
- 11381 : ノード
- 11380 : 中央サーバー
## インストール
YesCoinをダウンロードします
```
~$ git clone https://github.com/stsaria/yesCoin
```
ライブラリをインストールします
```
~yesCoin$ pip3 install -r requirements.txt
```
## 実行(ノード)
YesCoinを実行します
```
~yesCoin$ python3 src/main.py
初期中央サーバー(例: http://xxx.com:11380): 
```
と出るので、中央サーバーのURLを入力します
知らない場合は空のままで続行してください（エラーが出ますが、動きます）
空のままだと動機などの機能は利用できません。
ブラウザで http://127.0.0.1:11381 にアクセスします。
登録とかログインとかをすれば、完了です。
## 実行(中央サーバー)
※この中央サーバーでグローバルネットの通信をする際にはポート11380の開放が必要です
centralServer引数付きでYesCoinを実行します
```
~yesCoin$ python3 src/main.py centralServer
初期中央サーバー(例: http://xxx.com:11380): 
```
と出るので、知っている中央サーバーのURLを入力します。
知らない場合は空のままで続行してください（エラーは出ますが、動きます）
そうすると、自動的に処理が始まるのであとはSystemdなどで実行状態にしておくだけでOK
### サンプルコード
```/etc/systemd/system/yesCoin.service
[Unit]
Description=Virtual Coin - Yes Coin -
After=network.target

[Service]
WorkingDirectory=/home/stsaria/yesCoin

User=stsaria
Group=stsaria

Restart=always

ExecStart=/usr/bin/python3 src/main.py centralServer

[Install]
WantedBy=multi-user.target
```
## QRとかで送金する場合
QRとかGETの通信で送金する際は`sendUrl`を使います。
以下が例です
```
http://xxx.xxx.xxx.xxx:11381/sendUrl?recipient=送金先&amount=総金額
```
あと、これの処理にはログインが必要なので、
```
http://xxx.xxx.xxx.xxx:11381/login
```
のように、ログインのURLのQRコードも貼っておくと便利かもしれません。
## 制限
サーバーによっては手動の同期や、マイニングを禁止した場合もあるかもしれません。

その場合は
`DONTMINING`や`DONTMANUALSYNC`ファイルをyesCoinの直下に置くことによって禁止できます。
## 中央サーバーリストの吹っ飛び問題
プログラムで同期中にプログラムを停止すると中央サーバーリストが吹っ飛ぶ確率が高いです。
なので、`BOOTSTRAPSERVER`ファイルをyesCoinの直下において、に初期中央サーバーのURLを書いておくことを推奨します。(初期中央サーバーを設定したときに自動的に、書き込まれます。)
