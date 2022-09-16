#!/usr/bin/env python3
from logger_base.logger import Logger_base
from stella import StellaScraper, StellaDataType
from os.path import dirname, abspath, join

output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_stella.raw'
time_interval = 60
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

lockfile = join(dirname(abspath(__file__)), '.logger_stella.lock')
sockfile = join(dirname(abspath(__file__)), '.logger_stella.sock')

class LoggerStella(Logger_base):
    def initialize(self):
        self.dev = StellaScraper()
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
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.Temperature])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.Humidity])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.Pressure])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.PeakWindSpeed])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.WindSpeed])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.WindDirection])
                wstr += '  {0:.3f}'.format(ret_dict[StellaDataType.SolarZ])
                wstr += '  {0:.0f}'.format(ret_dict[StellaDataType.Brightness])
                wstr += '  {0:.4f}'.format(ret_dict[StellaDataType.Rain])
                wstr += '  {0:.4f}'.format(ret_dict[StellaDataType.Dust])

                self.write_data_to_file(wstr)
                self.last_update = dt

        except Exception as e:
            print(e)
            self.write_data_to_file('failed', header='# ')

if __name__ == '__main__':
    logger = LoggerStella(output_file_path=output_path,
                          file_header=file_header,
                          lock_file=lockfile,
                          sock_file=sockfile,
                          interval_sec=time_interval)

    logger.run(isDebug=False)
