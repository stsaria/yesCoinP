import threading, sys, os
mkDirs=["data", "config"]
for i in mkDirs:
    os.makedirs(i, exist_ok=True)
import centralApp, nodeApp

def main():
    print("YesCoin Start..")
    # 定期的に同期するためにスレッドを作る
    if len(sys.argv) > 1:
        if sys.argv[1] == "centralServer":
            syncThread = threading.Thread(target=centralApp.syncPeriodically)
            syncThread.daemon = True
            syncThread.start()
            centralApp.app.run(host='0.0.0.0', port=11380)
            return
    syncThread = threading.Thread(target=nodeApp.syncPeriodically)
    syncThread.daemon = True
    syncThread.start()
    nodeApp.app.run(host="0.0.0.0", port=11381)

if __name__ == "__main__":
    main()