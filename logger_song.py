#!/usr/bin/env python3
from logger_base.logger import Logger_base
from song import SongScraper, SongDataType
from os.path import dirname, abspath, join

output_path = '/home/gb/logger/data/weather/%Y/%m/%Y%m%d_song.raw'
time_interval = 10
file_header  = '## Localtime  Unixtime  '
file_header += 'Update UT  '
file_header += 'Temperature[degC]  '
file_header += 'Humidity[%]  '
file_header += 'WindSpeed[m/s]  '
file_header += 'Rain  '
file_header += 'Clouds  '
file_header += 'Dust  '
file_header += 'WindDir[degN]  '
file_header += 'DewPoint[degC]  '
file_header += 'Pressure[hPa]  '
file_header += '\n'

lockfile = join(dirname(abspath(__file__)), '.logger_song.lock')
sockfile = join(dirname(abspath(__file__)), '.logger_song.sock')

class LoggerSong(Logger_base):
    def initialize(self):
        self.dev = SongScraper()
        self.last_update = None

    def do(self):
        msg = self.sock_recv()
        if msg is not None:
            try:
                self.set_interval(float(msg))
            except:
                pass
            pass

        # read from song
        try:
            dt, ret_dict = self.dev.get()
            if self.last_update == dt:
                pass
            else:
                wstr =  '{0:.0f}'.format(dt.timestamp())
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.Temperature]))
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.Humidity]))
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.WindSpeed]))
                wstr += '  ' + ret_dict[SongDataType.Rain]
                wstr += '  ' + ret_dict[SongDataType.Clouds]
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.Dust]))
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.WindDir]))
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.DewPoint]))
                wstr += '  {0:.3f}'.format(float(ret_dict[SongDataType.Pressure]))

                self.write_data_to_file(wstr)
                self.last_update = dt

        except Exception as e:
            print(e)
            self.write_data_to_file('failed', header='# ')

if __name__ == '__main__':
    logger = LoggerSong(output_file_path=output_path,
                          file_header=file_header,
                          lock_file=lockfile,
                          sock_file=sockfile,
                          interval_sec=time_interval)

    logger.run(isDebug=False)
