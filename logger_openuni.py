#!/usr/bin/env python3
from logger_base.logger import Logger_base
from openuni import OpenuniScraper, OpenuniDataType
from os.path import dirname, abspath, join

output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_openuni.raw'
#output_path = './%Y%m%d_openuni.raw'

time_interval = 60

file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'AverageWindSpeed[km/h]  '
file_header += 'WindDirection[deg]  '
file_header += 'ExternalTemperature[degC]  '
file_header += 'ExternalHumidity[%]  '
file_header += 'StarCount  '
file_header += 'CloudBase[m]  '
file_header += 'Raining  '
file_header += '\n'

lockfile = join(dirname(abspath(__file__)), '.logger_openuni.lock')
sockfile = join(dirname(abspath(__file__)), '.logger_openuni.sock')

class LoggerOpenuni(Logger_base):
    def initialize(self):
        self.dev = OpenuniScraper()
        self.last_update = None

    def do(self):
        msg = self.sock_recv()
        if msg is not None:
            try:
                self.set_interval(float(msg))
            except:
                pass
            pass

        # read from stella
        try:
            dt, ret_dict = self.dev.get()
            if self.last_update == dt:
                pass
            else:
                wstr =  '{0:.0f}'.format(dt.timestamp())
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.AverageWindSpeed])
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.WindDirection])
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.ExternalTemperature])
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.ExternalHumidity])
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.StarCount])
                wstr += '  {0:.3f}'.format(ret_dict[OpenuniDataType.CloudBase])
                wstr += '  {}'.format(ret_dict[OpenuniDataType.Raining])

                self.write_data_to_file(wstr)
                self.last_update = dt

        except Exception as e:
            print(e)
            self.write_data_to_file('failed', header='# ')

if __name__ == '__main__':
    logger = LoggerOpenuni(output_file_path=output_path,
                          file_header=file_header,
                          lock_file=lockfile,
                          sock_file=sockfile,
                          interval_sec=time_interval)

    logger.run(isDebug=False)
