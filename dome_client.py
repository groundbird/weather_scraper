#!/usr/bin/env python3

'''Client software to read latest elevation data'''
import socket

IP_ADDRESS = '161.72.134.68'
PORT = 50000

class DomeClient:
    '''Client class to read latest elevation data
    '''
    def __init__(self, ip_addr=IP_ADDRESS, port=PORT):
        self._ip_addr = ip_addr
        self._port = port

    def get_status(self):
        '''Get status
        Returns
        -------
        res: str
            Response from the server
        '''
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(60)
        self._sock.connect((self._ip_addr, self._port))
        self._sock.send('d#status?'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def open(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(60)
        self._sock.connect((self._ip_addr, self._port))
        self._sock.send('d#open'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def close(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(60)
        self._sock.connect((self._ip_addr, self._port)) 
        self._sock.send('d#close'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def stop(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(60)
        self._sock.connect((self._ip_addr, self._port))
        self._sock.send('d#stop'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

    def ping(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(60)
        self._sock.connect((self._ip_addr, self._port))
        self._sock.send('d#'.encode('utf-8'))
        try:
            res = self._sock.recv(4096)
            res = b'OK'
        except:
            res = b'Timeout'
            import psutil, os
            pidlist = [str(proc.pid) for proc in psutil.process_iter() if len(proc.cmdline())>0 and 'dome_server' in str(proc.cmdline()[-1])]
            try:
                for pid in pidlist:
                    os.kill(int(pid), signal.SIGKILL) # kill(pid, sig)
            except:
                pass
        return str(res, encoding='UTF-8')
        
def main(com='status'):
    '''Main function'''
    domec = DomeClient()
    com = com.lower()[:4]
    if com == 'open':
        ret = domec.open()
    elif com == 'clos':
        ret = domec.close()
    elif com == 'stop':
        ret = domec.stop()
    elif com == 'stat':
        ret = domec.get_status()
    elif com == 'chec':
        ret = domec.ping()
    else:
        ret = f'Unknown command: {com}. Choose {open, close, stop}.'
        pass
    print(ret)

if __name__ == '__main__':
    import sys
    arg = sys.argv
    com = 'status'
    if len(arg)>1:
        com = arg[1]
        pass
    main(com)

