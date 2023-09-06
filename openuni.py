#!/usr/bin/env python3
import urllib3
import datetime

from datetime import timezone
from bs4 import BeautifulSoup
from enum import Enum

URL_STELLA = 'http://stella.aip.de/stella/status/status.php'
#URL_OPENUNI = 'https://www.telescope.org/weather.php'
URL_OPENUNI = 'https://www.telescope.org/weather.php'
#DTFORM_STELLA = 'Last environment data entry: %Y-%m-%d %H:%M:%S'
DTFORM_OPENUNI = '\nWeather information as of: %d/%m/%y %H:%M:%S'


class OpenuniDataType(Enum):
    AverageWindSpeed = 0     # km/h
    WindDirection = 1        # deg
    ExternalTemperature = 2  # Celsius
    ExternalHumidity = 3     # %
    StarCount = 4            #
    CloudBase = 5            # m
    Raining = 6                 #

class OpenuniScraper:
    def __init__(self, url=URL_OPENUNI):
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
            tab = bs.find_all('table')[0]
            for i,tr in enumerate(tab.find_all('tr')[1:]):
                if i < 6:
                    val = tr.find_all('td')[1].contents[0].split(' ')[0]
                    if val == '?':
                        val_list.append(float(-999))
                    else:
                        val_list.append(float(val))
                elif i == 6:
                    val_list.append(tr.find_all('td')[1].contents[0].split(' ')[0])
            assert len(val_list) == len(OpenuniDataType)
            # Update time
            dt = datetime.datetime.strptime(bs.find_all('p')[1].contents[0], DTFORM_OPENUNI)
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception as err:
            print(err)
            raise RuntimeError('Could not parse HTML.')

        ret_dict = {sdt:val_list[sdt.value] for sdt in OpenuniDataType}

        return dt, ret_dict

def main():
    openuni = OpenuniScraper()
    dt, data = openuni.get()
    print('Update: ', dt)
    for key, val in data.items():
        print(key.name, '\t', val)

if __name__ == '__main__':
    main()
