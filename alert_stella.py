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

input_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_stella.raw'
output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_stella.alert'

interval_read   = 61. # sec
interval_reopen = 351. # sec
interval_freeze = 1501. # sec

alert_time_interval = 1800. # sec

lockfile = '/home/gb/.gb_lock/alert_stella.lock'
sockfile = '/home/gb/.gb_sock/alert_stella.sock'

#lockfile = '/home/gb/alert_stella.lock'
#sockfile = '/home/gb/alert_stella.sock'

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


class StellaAlert(Controller_base):
    def initialize(self):
        self.write_data_to_file('== alert system start ==')
        contents = '== alert system start =='
        dt_now = datetime.now()
        self._to_addrs = None
        self.alert_en = True
        self.issue_alert = True
        self.send_alert(message=contents, data=None, now=dt_now, level=0)
        self.issue_alert = False
        # setting
        self.to_list  = None
        self._interval_read_ = interval_read
        self.alert_time_interval = alert_time_interval
        self._stop_freeze = False
        # internal parameter
        self.wind_level = -1
        self.wind_level_interval = -1
        self.dust_level = -1
        self.dust_level_interval = -1
        self.humd_level = -1
        self.humd_level_interval = -1
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
        if data is not None:
            body += '\n'.join([x + ' : ' + y for x, y in zip(file_header.split('  ')[2:], data)])
            pass
        self.alert('gbird.auto@gmail.com', self._to_addrs, body,
                   level=level, name='Stella',server_name=server_name)
    
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
    
    def close_dome(self):
        try:
            if self.alert_en:
                self.dome.close()
        except:
            self.send_alert('Dome cannot be closed.', wds, date_time, level=2)

    def control(self, date_time, data):
        self._stop_freeze = False
        self.read_comm()

        wds = data.split()
        d_wind_level = float(wds[5])/1000*3600 # km/h
        d_dust_level = float(wds[10]) # /m^3
        d_humd_level = float(wds[2]) # %
        d_is_rain    = float(wds[9]) / float(wds[8])>2e-7 # True/False
        
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

        # alert with time interval
        if self.wind_level_interval>-1:
            self.wind_level_interval += self._interval_read_
            if self.alert_en and self.wind_level_interval>self.alert_time_interval:
                contents = 'WindSpeed >40km/h for 30min'
                self.send_alert(message=contents, data=wds, now=date_time, level=1)
                self.wind_level_interval = -1
                #print("dome close")
                self.close_dome()

        if self.dust_level_interval>-1:
            self.dust_level_interval += 2*self._interval_read_
            if self.alert_en and self.dust_level_interval>self.alert_time_interval:
                contents = 'Dust >0.025/m3 for 15min'
                self.send_alert(message=contents, data=wds, now=date_time, level=1)
                self.dust_level_interval = -1
                #print("dome close")
                self.close_dome()
                
        if self.humd_level_interval>-1:
            self.humd_level_interval += self._interval_read_
            if self.alert_en and self.humd_level_interval>self.alert_time_interval:
                contents = 'Humidity >85% for 30min'
                self.send_alert(message=contents, data=wds, now=date_time, level=1)
                self.humd_level_interval = -1
                #print("dome close")
                self.close_dome()

        if self.rain_interval>-1:
            self.rain_interval += self._interval_read_
            if self.alert_en and self.rain_interval>self.alert_time_interval:
                contents = 'Not rain for 30min'
                self.send_alert(message=contents, data=wds, now=date_time, level=0)
                self.rain_interval = -1
                self.is_rain = False

        # alert: wind speed
        if d_wind_level > 45 and self.wind_level < 45:
            #contents = 'dome close test'
            contents = 'WindSpeed >45km/h'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.wind_level = 45
            if self.alert_en:
                self.wind_level_interval = -1
                #print("dome close")
                self.close_dome()
                pass
            pass
        
        if d_wind_level > 40 and self.wind_level < 40:
            contents = 'WindSpeed >40km/h'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.wind_level = 40
            self.wind_level_interval = 0
            pass
        
        if d_wind_level < 40 and self.wind_level == 40:
            self.wind_level_interval = -1
            pass

        if d_wind_level < 30 and self.wind_level > 30:
            contents = 'WindSpeed <30km/h'
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.wind_level = 30
            pass

        # alert: dust
        if d_dust_level > 0.025 and self.dust_level < 25:
            contents = 'Dust >0.025/m3'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.dust_level = 25
            self.dust_level_interval = 0
            pass

        if d_dust_level < 0.025 and self.dust_level == 25:
            self.dust_level_interval = -1
            pass
        
        if d_dust_level < 0.003 and self.dust_level > 3:
            contents = 'Dust <0.003/m3'
            self.send_alert(message=contents, data=wds, now=date_time, level=0)
            self.dust_level = 3
            pass
        
        # alert: humidity
        if d_humd_level > 90 and self.humd_level < 90:
            contents = 'Humidity >90%'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.humd_level = 90
            if self.alert_en:
                self.humd_level_interval = -1
                #print("dome close")
                self.close_dome()
                pass
            pass
        
        if d_humd_level > 85 and self.humd_level < 85:
            contents = 'Humidity >85%'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.humd_level = 85
            self.humd_level_interval = 0
            pass
        
        if d_humd_level < 85 and self.humd_level == 85:
            self.humd_level_interval = -1
            pass

        if d_humd_level > 80 and self.humd_level < 80:
            contents = 'Humidity > 80%'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.humd_level = 80
            pass

        if d_humd_level < 70 and self.humd_level == 90:
            self.humd_level = 70
            pass
        
        if d_humd_level > 60 and self.humd_level == 60:
            self.send_alert('Humidity >60%', wds, date_time, level=0)
            self.humd_level = 60
            pass
    
        #if d_humd_level < 60 and self.humd_level > 60:
        #    self.send_alert('Humidity <60%', wds, date_time, level=0)
        #    self.humd_level = 60
        #    pass

        if d_humd_level < 40 and self.humd_level > 40:
            self.send_alert('Humidity <40%', wds, date_time, level=0)
            self.humd_level = 40
            pass

        # alert: rain
        if d_is_rain and not self.is_rain:
            contents = 'Rain detected at stella'
            self.send_alert(message=contents, data=wds, now=date_time, level=1)
            self.is_rain = True
            if self.alert_en:
                #print("dome close")
                self.close_dome()
                pass
            pass
        if not d_is_rain and self.is_rain:
            self.rain_interval = 0
            self.is_rain = False
            pass

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
