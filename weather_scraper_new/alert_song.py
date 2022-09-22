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

input_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_song.raw'
output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_song.alert'

interval_read   = 61. # sec
interval_reopen = 801. # sec
interval_freeze = 2341. # sec

alert_time_interval = 3600. # sec

lockfile = '/home/gb/.gb_lock/alert_song.lock'
sockfile = '/home/gb/.gb_sock/alert_song.sock'

address_list_file = join(dirname(abspath(__file__)), 'mail_address_list.conf')

server_name = None

file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'Temperature[degC]  '
file_header += 'Humidity[%]  '
file_header += 'WindSpeed[m/s]  '
file_header += 'Rain  '
file_header += 'Clouds  '
file_header += 'Dust  '
file_header += 'WindDir[degN]  '
file_header += 'DewPoint[degC]  '
file_header += 'Pressure[hPa]  '
file_header += '\n'

if server_name is None:
    server_name = os.uname().nodename

class SongAlert(Controller_base):
    def initialize(self):
        self.write_data_to_file('== alert system start ==')
        # setting
        self.to_list  = None
        self.alert_en = True
        self.issue_alert = True
        self.alert_time_interval = alert_time_interval
        self._stop_freeze = False
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
        self.send_alert('no update data', data=None, now=dt_now, level=1)
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

	self.alert('gbird.auto@gmial.com', self._to_addrs, body,
                   level=level, name='Song',server_name=server_name)

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

        # info: enable/disable
        if self.issue_alert and self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system enable ==')
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.alert_en = True
            self.issue_alert = False
        elif self.issue_alert and not self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system disable ==')
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.alert_en = False
            self.issue_alert = False
        else:
            pass

        return

    pass

analert = SongAlert(input_file_path  = input_path,
                    output_file_path = output_path,
                    lock_file = lockfile,
                    sock_file = sockfile,
                    interval_read   = interval_read,
                    interval_reopen = interval_reopen,
                    interval_freeze = interval_freeze)

analert.run(isDebug = isDebug)
