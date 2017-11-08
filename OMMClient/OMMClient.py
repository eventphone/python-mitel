from threading import Thread
from xml.dom.minidom import parse, parseString
import rsa
import base64
import socket
import ssl
import Queue

TERMINATE_WORKER = "##EXIT##"

class OMMClient:

    tcp_socket = None
    ssl_socket = None
    send_q = None
    recv_q = None
    worker = None
    _sequence = 0

    def __init__(self,host, port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(10)
        self.ssl_socket = ssl.wrap_socket(self.tcp_socket)
        self.ssl_socket.connect((host, port))
        self.send_q = Queue.Queue()
        self.recv_q = Queue.Queue()
        self.worker = Thread(target=self.work)
        self.worker.daemon = True
        self.worker.start()

    def login(self,user,password):
        self._sequence += 1
        msg = '<Open protocolVersion="45" username="'
        msg += user
        msg += '" password="'
        msg += '" OMPClient="1" />'
        self.send_q.put(msg)

    def work(self):
        while True:
            if not self.send_q.empty():
                item = self.send_q.get(block=False)
                if item is TERMINATE_WORKER:
                    break
                self.ssl_socket.send(item + chr(0))
                self.send_q.task_done()
            self.ssl_socket.settimeout(0.1)
            data = None
            try:
                data = self.ssl_socket.recv(4096)
            except ssl.SSLError, e:
                if e.message == "The read operation timed out":
                    continue
            if data:
                self.recv_q.put(data)

    def __del__(self):
        self.send_q.put(TERMINATE_WORKER)
        self.ssl_socket.close()