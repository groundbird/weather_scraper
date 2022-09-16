#!/usr/bin/env python3
from logger_base.logger import Logger_base
from gaulli_download import GaulliDownloader, GaulliDownloadDataType
from os.path import dirname, abspath, join
import datetime
from logger_base.find_data_file import find_latest_file

output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_gaulli_final.raw'
time_interval = 60*60 # taken every 1 hour
file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'PWV final[mm]  '
file_header += 'Error[mm]  '
file_header += 'TZD[mm]  '
file_header += 'Pressure[hPa]  '
file_header += 'Temperature[degC]  '
file_header += 'Model/sensor  '
file_header += '\n'

lockfile = join(dirname(abspath(__file__)), '.logger_gaulli_final.lock')
sockfile = join(dirname(abspath(__file__)), '.logger_gaulli_final.sock')

class LoggerGaulliFinal(Logger_base):
    def initialize(self):
        self.dev = GaulliDownloader(pwv_type='p',num_days=5)
        self.last_update = None
        f = find_latest_file(self._output_file_path_)
        if f is not None:
            dt = datetime.datetime.fromtimestamp(float(open(f).readlines()[-1].split()[2]))
            self.last_update = dt

    def do(self):
        msg = self.sock_recv()
        if msg is not None:
            try:
                self.set_interval(float(msg))
            except:
                pass
            pass

        # read from gaulli
        #try:
        vallist = self.dev.get()
        for vals in vallist:
            dt = vals[0]
            ret_dict = vals[1]
            if self.last_update is not None and self.last_update >= dt:
                pass
            else:
                wstr = '{0}  {1:.1f}  {2:.1f}  {3:.1f}  {4:.1f}  {5:.1f}  {6}'.format(
                    dt.timestamp(),
                    ret_dict[GaulliDownloadDataType.PWV],
                    ret_dict[GaulliDownloadDataType.ERROR],
                    ret_dict[GaulliDownloadDataType.TZD],
                    ret_dict[GaulliDownloadDataType.PRESS],
                    ret_dict[GaulliDownloadDataType.TEMP],
                    ret_dict[GaulliDownloadDataType.METEO],
                )

                self.write_data_to_file(wstr, now=dt)
                self.last_update = dt

            #except Exception as e:
            #print(e)
            #self.write_data_to_file('failed', header='# ')

if __name__ == '__main__':
    logger = LoggerGaulliFinal(output_file_path=output_path,
                               file_header=file_header,
                               lock_file=lockfile,
                               sock_file=sockfile,
                               interval_sec=time_interval)
    
    logger.run(isDebug=True)
