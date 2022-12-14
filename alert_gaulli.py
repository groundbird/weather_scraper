#!/usr/bin/env python3
import os
from os.path import dirname, abspath, join
from pathlib import Path
import fcntl
import socket
from select import select
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate
from email.message import EmailMessage

from logger_base.controller import Controller_base
from dome_client import DomeClient

from datetime import datetime

isDebug = False

input_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_gaulli.raw'
output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_gaulli.alert'

interval_read   = 61. # sec
interval_reopen = 2001. # sec
interval_freeze = 10001. # sec

alert_time_interval = 10001. # sec

lockfile = '/home/gb/.gb_lock/alert_gaulli.lock'
sockfile = '/home/gb/.gb_sock/alert_gaulli.sock'

address_list_file = join(dirname(abspath(__file__)), 'mail_address_list.conf')

file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'PWV[mm]  '
file_header += 'PWV median(5d)[mm]  '
file_header += 'PWV mean(5d)[mm]  '
file_header += 'PWV std dev(5d)[mm]'
file_header += '\n'

server_name = os.uname().nodename

class GaulliAlert(Controller_base):
    def initialize(self):
        self.write_data_to_file('== alert system start ==')
        # setting
        self.to_list  = None
        self.alert_en = True
        self.issue_alert = True
        self.alert_time_interval = alert_time_interval
        self._stop_freeze = False
        self._to_addrs = None
        contents = '== alert system start=='
        dt_now=datetime.now()
        self.send_alert(message=contents, data='  ', now=dt_now, level=0)
        self.issue_alert = False
        # internal parameter
        # self.dome = DomeClient() # for dome operation
        return

    def finalize(self):
        self.write_data_to_file('== alert system stop ==')
        pass
    
    def freeze(self):
        if self._stop_freeze:
            return
        dt_now = datetime.now()
        self.send_alert('no update data', data='  ', now=dt_now, level=1)
        self._stop_freeze = True
        return

    def send_alert(self, message, data, now, level):
        if self._to_addrs is None:
            with open(address_list_file) as f:
                self._to_addrs = [_.strip() for _ in f if _[0] != '#']

        body = message + '\n'
        body += self._isotime_(now) + '\n'
        body += '  '.join(file_header.split('  ')[2:])
        body += '  '.join(data)
        
        self.alert('gbird.auto@gmail.com', self._to_addrs, body,
                   level=level, name='Gaulli',server_name=server_name)

        #self.alert('gbird.auto@gmail.com', 't.tanaka@astr.tohoku.ac.jp', body,
         #          level=level, name='Gaulli',server_name=server_name)

    def read_comm(self):
        buf = self.sock_recv()
        if buf is None: return
        try:
            wds = buf.split()
            if len(wds) != 2: return
            if wds[0] == 'alert_enable':
                if wds[1] in ['1', 'on', 'yes', 'True']:
                    self.issue_alert = True
                    self.alert_en = True
                else:
                    self.issue_alert = True
                    self.alert_en = False
                    pass
                pass
            pass
        except Exception as e:
            #print(e)
            pass
        return
    
    def control(self, date_time, data):
        self._stop_freeze = False
        self.read_comm()

        wds = data.split()
        
        #self.send_alert(message='test', data='test', now=dt_now, level=0)
        
        # info: enable/disable
        if self.issue_alert and self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system enable ==')
            contents = '== alert system enable =='
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.alert_en = True
            self.issue_alert = False
            
        elif self.issue_alert and not self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system disable ==')
            contents = '== alert system disable =='
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.alert_en = False
            self.issue_alert = False
        else:
            pass

        return

    pass

analert = GaulliAlert(input_file_path  = input_path,
                      output_file_path = output_path,
                      lock_file = lockfile,
                      sock_file = sockfile,
                      interval_read = interval_read,
                      interval_reopen = interval_reopen,
                      interval_freeze = interval_freeze)

"""
from logger_base.base import Base


line ="2022-09-19T02:10:11.797298+00:00  1663553411.797298  1663552800.0  5.3  8.4  8.2  2.2"

dt, data = Base()._divide_datetime_data_(line)
analert.control(date_time = dt, data = data)
"""

analert.run(isDebug = isDebug)
