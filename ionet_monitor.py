import requests
import json
import time
from datetime import datetime
import os
import config

def getDeviceSummary(deviceId):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0',
            'Token': config.common['Token']
        }

        url = f"https://api.io.solutions/v1/io-worker/devices/{deviceId}/summary"
        r = requests.get(url, headers=headers)
        print(r.text)
        summary = json.loads(r.text)

        if summary["status"] != 'succeeded':
            return None

        return summary

    except Exception as e:
        print(f"getDeviceSummary exception: {deviceId}")
        print(e)
        return None

def run():
    if config.common['System'] == 'mac':
        process = "./launch_binary_mac"
        systemParam = '--operating_system="macOS"'
    else:
        process = "./launch_binary_linux"
        systemParam = '--operating_system="linux"'
    if config.common['UseGpus']:
        gpuParam = '--usegpus=true'
    else:
        gpuParam = '--usegpus=false'
    cmd = f"{process} --device_id={config.common['DeviceId']} --user_id={config.common['UserId']} {systemParam} {gpuParam} --device_name={config.common['DeviceName']}"
    print(cmd)
        
    lastDownTime = None
    while True:
        now = datetime.now()
        ts = now.strftime('%Y-%m-%d %H:%M:%S')
        print(ts)

        summary = getDeviceSummary(config.common["DeviceId"])
        if summary is not None:
            data = summary["data"]
            print(f"id:{data['device_id']}, name:{data['device_name']}, download_speed_mbps:{data['download_speed_mbps']}, upload_speed_mbps:{data['upload_speed_mbps']}, status:{data['status']}")

            if data["status"] == 'up':
                lastDownTime = None
            else:
                if lastDownTime is None:
                    lastDownTime = time.time()
                else:
                    if time.time() - lastDownTime >= config.common["RestartMinute"]*60:
                        print("Restart ionet")
                        result = os.popen(cmd)
                        print(result.read())
                        lastDownTime = None

        time.sleep(config.common["IntervalMinute"]*60)

if __name__ == '__main__':
    run()

