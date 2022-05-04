import base64
import json
import time
import requests

URL = 'http://127.0.0.1:8000/tts'


def tts(message):
    datas = {'message': message}
    headers = {'Content-Type': 'application/json'}
    t0 = time.time()
    r = requests.get(URL, params=datas)
    t1 = time.time()
    r.encoding = 'utf-8'
    result = json.loads(r.text)
    print(result)
    print('time:', t1 - t0, 's')


if __name__ == '__main__':
    tts('你好呀，我是艾融小张！')
