#!/usr/bin/env python
# -*- encoding=utf8 -*-

import time
import requests
import json

from datetime import datetime, timedelta

from .jd_logger import logger
from .config import global_config


class Timer(object):
    def __init__(self, sleep_interval=0.2):
        # '2018-09-28 22:45:50.000'
        self.buy_time = datetime.strptime(global_config.getRaw('config', 'buy_time'), "%Y-%m-%d %H:%M:%S.%f")
        target = datetime.now()
        if target.hour > self.buy_time.hour:
            # 当天已过抢购时间，则顺延到下一天
            target += timedelta(days=1)
        if self.buy_time < target:
            # 若时间已过则自动调整为下一个抢购时间
            self.buy_time = self.buy_time.replace(year=target.year, month=target.month, day=target.day)
        self.buy_time_ms = int(time.mktime(self.buy_time.timetuple()) * 1000.0 + self.buy_time.microsecond / 1000)
        self.sleep_interval = sleep_interval

        self.diff_time = self.local_jd_time_diff()
        print(target, self.buy_time, self.diff_time)

    def jd_time(self):
        """
        从京东服务器获取时间毫秒
        :return:
        """
        url = 'https://a.jd.com//ajax/queryServerData.html'
        ret = requests.get(url).text
        js = json.loads(ret)
        return int(js["serverTime"])

    def local_time(self):
        """
        获取本地毫秒时间
        :return:
        """
        return int(round(time.time() * 1000))

    def local_jd_time_diff(self):
        """
        计算本地与京东服务器时间差
        :return:
        """
        # 多次获取消除网络延时误差
        count = 10
        sum = 0
        for _ in range(count):
            l = self.local_time()
            j = self.jd_time()
            sum += (l - j)
            print(l, j)
            time.sleep(0.1)
        return sum / count

    def start(self):
        logger.info('正在等待到达设定时间:{}，检测本地时间与京东服务器时间误差为【{}】毫秒'.format(self.buy_time, self.diff_time))
        while True:
            # 本地时间减去与京东的时间差，能够将时间误差提升到0.1秒附近
            # 具体精度依赖获取京东服务器时间的网络时间损耗
            if self.local_time() - self.diff_time >= self.buy_time_ms:
                logger.info('时间到达，开始执行……')
                break
            else:
                time.sleep(self.sleep_interval)
