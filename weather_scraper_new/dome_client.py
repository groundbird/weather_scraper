#!/usr/bin/env python3

'''Client software to read latest elevation data'''
import socket

IP_ADDRESS = '161.72.134.68'
DOME_PORT = 9873

class DomeClient:
    '''Client class to read latest elevation data
    '''
    def __init__(self, ip_addr=IP_ADDRESS, port=DOME_PORT):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ip_addr = ip_addr
        self._port = port
        self._sock.connect((self._ip_addr, self._port))

    def get_status(self):
        '''Get status
        Returns
        -------
        res: str
            Response from the server
        '''
        self._sock.send('d#status?'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def open(self):
        self._sock.send('d#open'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def close(self):
        self._sock.send('d#close'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def stop(self):
        self._sock.send('d#stop'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

def main(com=None):
    '''Main function'''
    domec = DomeClient()
    if com is not None:
        com = com.lower()[:4]
        if com == 'open':
            domec.open()
        elif com == 'clos':
            domec.close()
        elif com == 'stop':
            domec.stop()
        else:
            print(f'Unknown command: {com}. Choose {open, close,stop}.')
        pass
    else:
        print(domec.get_status())
        pass

if __name__ == '__main__':
    import sys
    arg = sys.argv
    if len(arg)>1:
        main(arg[1])
    else:
        main()

