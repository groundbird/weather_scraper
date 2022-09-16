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

isDebug = True

input_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_stella.raw'
output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_stella.alert'

interval_read   = 61. # sec
interval_reopen = 351. # sec
interval_freeze = 1501. # sec

alert_time_interval = 1800. # sec

lockfile = '/home/gb/.gb_lock/alert_stella.lock'
sockfile = '/home/gb/.gb_sock/alert_stella.sock'

address_list_file = join(dirname(abspath(__file__)), 'mail_address_list.conf')

server_name = None

file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'Temperature[degC]  '
file_header += 'Humidity[%]  '
file_header += 'Pressure[hPa]  '
file_header += 'PeakWindSpeed[m/s]  '
file_header += 'WindSpeed[m/s]  '
file_header += 'WindDirection[deg]  '
file_header += 'SolarZ[deg]  '
file_header += 'Brightness[Lux]  '
file_header += 'Rain  '
file_header += 'Dust[m^{-3}]  '
file_header += '\n'

if server_name is None:
    server_name = os.uname().nodename

def send_via_gmail(msg, to_addrs=None, from_addr='shugo.auto@gmail.com'): #from_addr, to_addr, msg):
    if to_addrs is None:
        with open(address_list_file) as f:
            to_addrs = [_.strip() for _ in f if _[0] != '#']
    for i in range(10):
        try:
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login('shugo.auto@gmail.com', 'Cf:+S]]3<kAe>ti:')
            s.send_message(msg, from_addr, to_addrs)
            s.close()
            break
        except OSError:
            sleep(20)
        except Exception as e:
            #print(e)
            pass

def make_message(from_addr, to_addr, subject, text):
    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate()
    return msg

class StellaAlert(Controller_base):
    def initialize(self):
        self.write_data_to_file('== alert system start ==')
        # setting
        self.to_list  = None
        self.alert_en = True
        self.issue_alert = True
        self.alert_time_interval = alert_time_interval
        self._stop_freeze = False
        # internal parameter
        self.wind_level = -1
        self.wind_level_interval = -1
        self.dust_level = -1
        self.dust_level_interval = -1
        self.is_rain = False
        self.rain_interval = -1
        self.dome = DomeClient()
        return

    def finalize(self):
        self.write_data_to_file('== alert system stop ==')
        pass

    def freeze(self):
        if self._stop_freeze:
            return
        self.alert('no update data', level=1)
        self._stop_freeze = True
        return

    def control(self, date_time, data):
        self._stop_freeze = False
        self.read_comm()

        wds = data.split()
        d_wind_level = float(wds[5])/1000*3600 # km/h
        d_dust_level = float(wds[10]) # /m^3
        d_is_rain    = float(wds[9])>1e-6 # True/False

        # info: enable/disable
        if self.issue_alert and self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system enable ==')
            self.alert('== alert system enable ==', wds, date_time, level=0)
            self.alert_en = True
            self.issue_alert = False
        elif self.issue_alert and not self.alert_en:
            self.alert_en = True # temporally true to issue the alert
            self.write_data_to_file('== alert system disable ==')
            self.alert('== alert system disable ==', wds, date_time, level=0)
            self.alert_en = False
            self.issue_alert = False
        else:
            pass

        # alert with time interval
        if self.wind_level_interval>-1:
            self.wind_level_interval += self._interval_read_
            if self.alert_en and self.wind_level_interval>self.alert_time_interval:
                self.alert('WindSpeed >40km/h for 30min', wds, date_time, level=1)
                self.wind_level_interval = -1
                #print("dome close")
                self.dome.close()

        if self.dust_level_interval>-1:
            self.dust_level_interval += 2*self._interval_read_
            if self.alert_en and self.dust_level_interval>self.alert_time_interval:
                self.alert('Dust >0.025/m3 for 15min', wds, date_time, level=1)
                self.dust_level_interval = -1
                #print("dome close")
                self.dome.close()

        if self.rain_interval>-1:
            self.rain_interval += self._interval_read_
            if self.alert_en and self.rain_interval>self.alert_time_interval:
                self.alert('Not rain for 30min', wds, date_time, level=0)
                self.rain_interval = -1
                self.is_rain = False

        # alert: wind speed
        if d_wind_level > 45 and self.wind_level < 45:
            self.alert('WindSpeed >45km/h', wds, date_time, level=1)
            self.wind_level = 45
            if self.alert_en:
                self.wind_level_interval = -1
                #print("dome close")
                self.dome.close()
                pass
            pass
        if d_wind_level > 40 and self.wind_level < 40:
            self.alert('WindSpeed >40km/h', wds, date_time, level=1)
            self.wind_level = 40
            self.wind_level_interval = 0
            pass
        if d_wind_level < 40 and self.wind_level == 40:
            self.wind_level_interval = 0
            pass
        if d_wind_level < 30 and self.wind_level > 30:
            self.alert('WindSpeed <30km/h', wds, date_time, level=0)
            self.wind_level = 30
            self.wind_level_interval = -1
            pass

        # alert: dust
        if d_dust_level > 0.025 and self.dust_level < 25:
            self.alert('Dust >0.025/m3', wds, date_time, level=1)
            self.dust_level = 25
            self.dust_level_interval = 0
            pass
        if d_dust_level < 0.025 and self.dust_level == 25:
            self.dust_level_interval = 0
            pass
        if d_dust_level < 0.003 and self.dust_level > 3:
            self.alert('Dust <0.003/m3', wds, date_time, level=0)
            self.dust_level = 3
            self.dust_level_interval = -1
            pass

        # alert: rain
        if d_is_rain and not self.is_rain:
            self.alert('Rain detected at stella', wds, date_time, level=1)
            self.is_rain = True
            if self.alert_en:
                #print("dome close")
                self.dome.close()
                pass
            pass
        if not d_is_rain and self.is_rain:
            self.rain_interval = 0
            pass
        if d_is_rain and self.is_rain:
            self.rain_interval = 0
            pass

        return

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

    def alert(self, body, data=None, now=None, level=0):
        self.write_data_to_file(body)
        if not self.alert_en: return
        title = '[Stella]'
        if level == 0: # info
            title += ' INFO from {}'.format(server_name)
        elif level == 1: # alert
            title += ' ALERT from {}'.format(server_name)
        elif level == 2: # emergency
            title += ' EMERGENCY from {}'.format(server_name)
        else:
            title += ' MESSAGE from {}'.format(server_name)

        body += '\n'
        if now is not None:
            body += self._isotime_(now) + '\n'
        if data is not None:
            body += '  '.join(file_header.split('  ')[2:])
            body += '  '.join(data)
 
        self.sendmail(title, body)

    def sendmail(self, title, body):
        m = make_message('stella_alert@{}'.format(server_name),
	                 'User@{}'.format(server_name),
                         title, body)
        send_via_gmail(m)
        return

    pass

analert = StellaAlert(input_file_path  = input_path,
                      output_file_path = output_path,
                      lock_file = lockfile,
                      sock_file = sockfile,
                      interval_read   = interval_read,
                      interval_reopen = interval_reopen,
                      interval_freeze = interval_freeze)

analert.run(isDebug = isDebug)
