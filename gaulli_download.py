#!/usr/bin/env python3
import urllib3
import urllib.request, urllib.error

import ssl

import datetime
import os

from datetime import timezone
from bs4 import BeautifulSoup
from enum import IntEnum

URL_GAULLI = 'https://gaulli2.ll.iac.es/OT'
DTFORM_GAULLI = '%Y/%m/%d - %H:%M UTC'
FNAME_TMP = 'latest.txt'

class GaulliDownloadDataType(IntEnum):
    PWV      = 0      # mm
    ERROR    = 1      # mm
    TZD      = 2      # mm
    PRESS    = 3      # hPa
    TEMP     = 4      # degC
    METEO    = 5      # model/sensor

class GaulliDownloader:
    def __init__(self, url=URL_GAULLI, pwv_type='p', num_days=30):
        self._url = url
        self._pwv_type = pwv_type # "r": rapid=express, "p": precise=final
        self._num_days = num_days # days to be downloaded at each time, should be >2 if pwv_type="p"

    def get(self):
        os.system(f"wget --no-check-certificate --post-data \'pwv_type={self._pwv_type}&num_days_download={self._num_days}\'  {self._url} -O {FNAME_TMP}")# > /dev/null 2> /dev/null")
        print(f"wget --no-check-certificate --post-data 'pwv_type={self._pwv_type}&num_days_download={self._num_days}'  {self._url} -O {FNAME_TMP} > /dev/null 2> /dev/null")
        f = open(FNAME_TMP)
        lines = f.readlines()
        vals = [line.strip().strip('\"\'').split(',') for line in lines if line.strip().strip('\"\'')[0]!='#']
        def convert(val):
            # DATE[yyyy/mm/dd],UT[HH:MM],PWV_final[mm],ERROR[mm],TZD_final[mm],PRESS[Hpa],TEMP[C],METEO_DATA[model/sensor]
            t = datetime.datetime.strptime(val[0]+val[1], "%Y/%m/%d%H:%M")
            v = [float(x) for x in val[2:-1]] + [val[-1]]
            return (t,v)
        vals = [convert(ival) for ival in vals]

        return vals

def main():
    gaulli = GaulliDownloader()
    vals = gaulli.get()
    print(len(vals))
    dt,data = vals[-1]

    print('Update: ', dt, data[-1])
    for val in data[:-1]:
        print(val)
        print(data)

if __name__ == '__main__':
    main()
