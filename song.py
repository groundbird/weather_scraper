#!/usr/bin/env python3
import urllib3
import datetime

from datetime import timezone
from bs4 import BeautifulSoup
from enum import IntEnum

#URL_SONG = 'http://song.phys.au.dk/weatherpage/'
URL_SONG = 'https://song.phys.au.dk/tenerife/weatherpage/'
DTFORM_SONG = 'Last updated: %Y-%m-%d %H:%M:%S UTC'

class SongDataType(IntEnum):
    Temperature = 0
    Humidity = 1
    WindSpeed = 2
    Rain = 3
    Clouds = 4
    Dust = 5
    WindDir = 6
    DewPoint = 7
    Pressure = 8

class SongScraper:
    def __init__(self, url=URL_SONG):
        self._http = urllib3.PoolManager()
        self._url = url

    def get(self):
        r = self._http.request('GET', self._url)
        if r.status != 200:
            raise RuntimeError('HTTP error {0}: {1}'.format(r.status, self._url))
        bs = BeautifulSoup(r.data, 'html.parser')

        val_list = []
        try:
            # Fetch table
            tab = bs.find_all('table')[7]
            for tr in tab.find_all('tr'):
                valstr = tr.find_all('td')[1].contents[0].lstrip().rstrip()
                val_list.append(valstr)

            val_list = val_list + ['100', '0'] #no data [DewPoint, Pressure]

            assert len(val_list) == len(SongDataType)

            # Update time
            timestr = bs.find_all("table")[1].find_all("td")[1].get_text()
            dt = datetime.datetime.strptime(timestr, DTFORM_SONG)
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception as err:
            print(err)
            raise RuntimeError('Could not parse HTML.')

        ret_dict = {sdt:val_list[sdt.value] for sdt in SongDataType}

        return dt, ret_dict

def main():
    stella = SongScraper()

    dt, data = stella.get()
    print('Update: ', dt)
    for key, val in data.items():
        print(key.name, '\t', val)

if __name__ == '__main__':
    main()
