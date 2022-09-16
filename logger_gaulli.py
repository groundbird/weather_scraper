#!/usr/bin/env python3
from logger_base.logger import Logger_base
from gaulli import GaulliScraper, GaulliDataType
from os.path import dirname, abspath, join

output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_gaulli.raw'
time_interval = 60
file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'PWV[mm]  '
file_header += 'PWV median(5d)[mm]  '
file_header += 'PWV mean(5d)[mm]  '
file_header += 'PWV std dev(5d)[mm]'
file_header += '\n'

lockfile = join(dirname(abspath(__file__)), '.logger_gaulli.lock')
sockfile = join(dirname(abspath(__file__)), '.logger_gaulli.sock')

class LoggerGaulli(Logger_base):
    def initialize(self):
        self.dev = GaulliScraper()
        self.last_update = None

    def do(self):
        msg = self.sock_recv()
        if msg is not None:
            try:
                self.set_interval(float(msg))
            except:
                pass
            pass

        # read from gaulli
        try:
            dt, ret_dict = self.dev.get()
            if self.last_update == dt:
                pass
            else:
                wstr = '{0}  {1:.1f}  {2:.1f}  {3:.1f}  {4:.1f}'.format(
                    dt.timestamp(),
                    ret_dict[GaulliDataType.PWV],
                    ret_dict[GaulliDataType.PWV_med],
                    ret_dict[GaulliDataType.PWV_mean],
                    ret_dict[GaulliDataType.PWV_std]
                )

                self.write_data_to_file(wstr)
                self.last_update = dt

        except Exception as e:
            print(e)
            self.write_data_to_file('failed', header='# ')

if __name__ == '__main__':
    logger = LoggerGaulli(output_file_path=output_path,
                          file_header=file_header,
                          lock_file=lockfile,
                          sock_file=sockfile,
                          interval_sec=time_interval)

    logger.run(isDebug=False)
