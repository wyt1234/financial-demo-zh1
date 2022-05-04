#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2016-2099 Ailemon.net
#
# This file is part of ASRT Speech Recognition Tool.
#
# ASRT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# ASRT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ASRT.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================================

'''
@author: nl8590687
ASRT语音识别asrserver http协议测试专用客户端
'''
import base64
import json
import time
import requests
import wave


def read_wav_bytes(filename: str) -> tuple:
    '''
    读取一个wav文件，返回声音信号的时域谱矩阵和播放时间
    '''
    wav = wave.open(filename, "rb")  # 打开一个wav格式的声音文件流
    num_frame = wav.getnframes()  # 获取帧数
    num_channel = wav.getnchannels()  # 获取声道数
    framerate = wav.getframerate()  # 获取帧速率
    num_sample_width = wav.getsampwidth()  # 获取实例的比特宽度，即每一帧的字节数
    str_data = wav.readframes(num_frame)  # 读取全部的帧
    wav.close()  # 关闭流
    return str_data, framerate, num_channel, num_sample_width


def asr(file_path=None, b64wave: str = None):
    URL = 'http://127.0.0.1:20001/all'
    if not b64wave:
        wav_bytes, sample_rate, channels, sample_width = read_wav_bytes(file_path)
        datas = {
            'channels': channels,
            'sample_rate': sample_rate,
            'byte_width': sample_width,
            'samples': str(base64.urlsafe_b64encode(wav_bytes), encoding='utf-8')
        }
    else:
        b64wave = str(base64.urlsafe_b64encode(base64.b64decode(b64wave)), encoding='utf-8')
        datas = {
            'channels': 1,
            'sample_rate': 16000,
            'byte_width': 2,
            'samples': b64wave
        }
    headers = {'Content-Type': 'application/json'}
    t0 = time.time()
    r = requests.post(URL, headers=headers, data=json.dumps(datas))
    t1 = time.time()
    r.encoding = 'utf-8'
    result = json.loads(r.text)
    print(result)
    print('time:', t1 - t0, 's')
    return result['result']
