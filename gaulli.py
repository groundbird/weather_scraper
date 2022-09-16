#!/usr/bin/env python3
import urllib3
import urllib.request, urllib.error

import ssl

import datetime

from datetime import timezone
from bs4 import BeautifulSoup
from enum import IntEnum

URL_GAULLI = 'https://gaulli2.ll.iac.es/OT'
DTFORM_GAULLI = '%Y/%m/%d - %H:%M UTC'

class GaulliDataType(IntEnum):
    PWV      = 0      # mm
    PWV_med  = 1      # mm
    PWV_mean = 2      # mm
    PWV_std  = 3      # mm

class GaulliScraper:
    def __init__(self, url=URL_GAULLI):
        self._url = url
        self._req = urllib.request.Request(url=self._url)
        self._context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)


    def get(self):
        f = urllib.request.urlopen(self._req,context=self._context)
        r = f.read()
        bs = BeautifulSoup(r, 'html.parser')

        val_list = [None]*len(GaulliDataType)
        try:
            # Fetch table
            vals = bs.find("main").find("div",{"class":"row text-center dashboard"}).find_all("div",{"class":"card"})
            for i in GaulliDataType:
                tmp = [x.get_text().rstrip().lstrip() for x in vals[int(i)].contents if x!='\n']
                # [0]: name, [1]: value + " mm", [2]: time (only available in Express (GaulliDataType.PWV) column)
                if len(tmp)>2: timestr = tmp[2]
                val_list[i] = float(tmp[1].split(" ")[0])

            assert len(val_list) == len(GaulliDataType)

            dt = datetime.datetime.strptime(timestr, DTFORM_GAULLI)
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception as err:
            print(err)
            raise RuntimeError('Could not parse HTML.')

        ret_dict = {sdt:val_list[sdt.value] for sdt in GaulliDataType}

        return dt, ret_dict

def main():
    gaulli = GaulliScraper()

    dt, data = gaulli.get()
    print('Update: ', dt)
    for key, val in data.items():
        print(key.name, '\t', val)

if __name__ == '__main__':
    main()

