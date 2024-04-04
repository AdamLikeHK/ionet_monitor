import requests
import json
import time
from datetime import datetime
import os
import config

class IONetMonitor():
    def __init__(self):
        self.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0'

        self.refreshToken = config.common['RefreshToken']

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
        self.cmd = f"{process} --device_id={config.common['DeviceId']} --user_id={config.common['UserId']} {systemParam} {gpuParam} --device_name={config.common['DeviceName']}"

        if config.common['LogLevel'] <= 0:
            print(self.cmd)

    def refresh(self):
        try:
            headers = {
                'User-Agent': self.userAgent,
                'Content-Type': 'application/json',
                'Apikey': config.common['Apikey'],
                'Authorization': config.common['Authorization']
            }

            url = f"https://id.io.net/auth/v1/token?grant_type=refresh_token"
            data = {"refresh_token": config.common['RefreshToken']}
            r = requests.post(url, headers=headers, json=data)
        
            if config.common['LogLevel'] <= 0:
                print(r.text)
        
            info = json.loads(r.text)

            if 'access_token' not in info:
                print(info)
                return False
            self.accessToken = info['access_token']
            self.refreshToken = info['refresh_token']
            self.userId = info['user']['id']
            self.userEmail = info['user']['email']
            print(f"RefreshToken:{self.refreshToken}, id:{self.userId}, email:{self.userEmail}")
            
            return True

        except Exception as e:
            print(f"refresh exception: {deviceId}")
            print(e)
            return False

    def getDeviceSummary(self, deviceId):
        try:
            headers = {
                'User-Agent': self.userAgent,
                'Token': self.accessToken
            }

            url = f"https://api.io.solutions/v1/io-worker/devices/{deviceId}/summary"
            r = requests.get(url, headers=headers)
    
            if config.common['LogLevel'] <= 0:
                print(r.text)

            summary = json.loads(r.text)

            if summary["status"] != 'succeeded':
                return None

            return summary

        except Exception as e:
            print(f"getDeviceSummary exception: {deviceId}")
            print(e)
            return None

    def devicesList(self, userId, page, pageSize):
        try:
            headers = {
                'User-Agent': self.userAgent,
                'Token': self.accessToken
            }

            url = f"https://api.io.solutions/v1/io-worker/users/{userId}/devices?page={page}&page_size={pageSize}"
            r = requests.get(url, headers=headers)

            if config.common['LogLevel'] <= 0:
                print(r.text)

            res = json.loads(r.text)

            if res["status"] != 'succeeded':
                return None

            devices = res['data']['devices']
            return devices

        except Exception as e:
            print(f"devicesList exception: {deviceId}")
            print(e)
            return None

    def stats(self):
        now = datetime.now()
        ts = now.strftime('%Y-%m-%d %H:%M:%S')
        print(ts)

        if not self.refresh():
            return False
        devices = self.devicesList(self.userId, 1, 20)
        if devices is None:
            return False

        if config.common['LogLevel'] <= 0:
            print(devices)

        for device in devices:
            summary = self.getDeviceSummary(device['device_id'])
            if summary is not None:
                data = summary["data"]
                print(f"id:{data['device_id']}, name:{data['device_name']}, download_speed_mbps:{data['download_speed_mbps']}, upload_speed_mbps:{data['upload_speed_mbps']}, connectivity_tier:{data['connectivity_tier']}, status:{data['status']}")

    def start(self):
        lastDownTime = None
        while True:
            now = datetime.now()
            ts = now.strftime('%Y-%m-%d %H:%M:%S')
            print(ts)

            if not self.refresh():
                print("Refresh token fail, exit.")
                break

            summary = self.getDeviceSummary(config.common["DeviceId"])
            if summary is not None:
                data = summary["data"]
                print(f"id:{data['device_id']}, name:{data['device_name']}, download_speed_mbps:{data['download_speed_mbps']}, upload_speed_mbps:{data['upload_speed_mbps']}, connectivity_tier:{data['connectivity_tier']}, status:{data['status']}")

                if data["status"] == 'up':
                    lastDownTime = None
                else:
                    if lastDownTime is None:
                        lastDownTime = time.time()
                    else:
                        if time.time() - lastDownTime >= config.common["RestartMinute"]*60:
                            print("Restart ionet")
                            result = os.popen(self.cmd)
                            print(result.read())
                            lastDownTime = None

            time.sleep(config.common["IntervalMinute"]*60)

def run():
    monitor = IONetMonitor()
    # monitor.refresh()
    monitor.start()

if __name__ == '__main__':
    run()

