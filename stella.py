#!/usr/bin/env python3
import urllib3
import datetime

from datetime import timezone
from bs4 import BeautifulSoup
from enum import Enum

#URL_STELLA = 'http://stella.aip.de/stella/status/status.php'
URL_STELLA = 'http://stella-archive.aip.de/stella/status/status.php'
DTFORM_STELLA = 'Last environment data entry: %Y-%m-%d %H:%M:%S'


class StellaDataType(Enum):
    Temperature = 0   # deg C
    Humidity = 1      # %
    Pressure = 2      # hPa
    PeakWindSpeed = 3 # m/s
    WindSpeed = 4     # m/s
    WindDirection = 5 # deg
    SolarZ = 6        # deg
    Brightness = 7    # Lux
    Rain = 8          #
    Dust = 9          # m^{-3}

class StellaScraper:
    def __init__(self, url=URL_STELLA):
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
            tab = bs.find_all('table')[1]
            for tr in tab.find_all('tr')[1:]:
                val_list.append(float(tr.find_all('td')[1].find('a').contents[0]))
            assert len(val_list) == len(StellaDataType)
            
            # Update time
            dt = datetime.datetime.strptime(bs.find_all('p')[1].contents[0], DTFORM_STELLA)
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception as err:
            print(err)
            raise RuntimeError('Could not parse HTML.')

        ret_dict = {sdt:val_list[sdt.value] for sdt in StellaDataType}

        return dt, ret_dict

def main():
    stella = StellaScraper()

    dt, data = stella.get()
    print('Update: ', dt)
    for key, val in data.items():
        print(key.name, '\t', val)

if __name__ == '__main__':
    main()
