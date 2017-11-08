from threading import Thread,Event,Lock
from time import sleep
from utils import *
from messagehelper import *
import socket
import ssl
import Queue


class OMMClient:
    tcp_socket = None
    ssl_socket = None
    send_q = None
    recv_q = None
    _worker = None
    _dispatcher = None
    _sequence = 0
    _terminate = False
    _events = {}
    _eventlock = Lock()
    _modulus = None
    _exponent = None
    omm_status = {}

    def __init__(self, host, port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(10)
        self.ssl_socket = ssl.wrap_socket(self.tcp_socket)
        self.ssl_socket.connect((host, port))
        self.send_q = Queue.Queue()
        self.recv_q = Queue.Queue()
        self._worker = Thread(target=self._work)
        self._worker.daemon = True
        self._worker.start()
        self._dispatcher = Thread(target=self._dispatch)
        self._dispatcher.daemon = True
        self._dispatcher.start()

    def _awaitresponse(self,message):
        if message in self._events:
            raise Exception("Alread waiting for "+message)
        e = Event()
        with self._eventlock:
            self._events[message] = {}
            self._events[message]["event"] = e
        self._events[message]["event"].wait()
        return self._events[message]["response"]

    def login(self, user, password):
        self._sequence += 1
        messagedata = {
            "protocolVersion": "45",
            "username": user,
            "password": password,
            "OMPClient": "1"
        }
        msg = construct_single_message("Open", messagedata)
        self.send_q.put(msg)
        message, attributes, children = parse_message(self._awaitresponse("OpenResp"))
        self._modulus = children["publicKey"]["modulus"]
        self._exponent = children["publicKey"]["exponent"]
        self.omm_status = attributes

    def _work(self):
        while not self._terminate:
            print("_work loop")
            if not self.send_q.empty():
                item = self.send_q.get(block=False)
                self.ssl_socket.send(item + chr(0))
                self.send_q.task_done()
            self.ssl_socket.settimeout(1.1)
            data = None
            try:
                data = self.ssl_socket.recv(4096)
            except ssl.SSLError, e:
                if e.message == "The read operation timed out":
                    continue
            if data:
                self.recv_q.put(data)

    def _dispatch(self):
        while not self._terminate:
            print("_dispatch loop")
            sleep(0.1)
            if not self.recv_q.empty():
                item = self.recv_q.get(block=False)
                message, attributes, children = parse_message(item)
                with self._eventlock:
                    if message in self._events:
                            self._events[message]["response"] = item
                            self._events[message]["event"].set()

    def logout(self):
        self._terminate = True
        self._worker.join()
        self._dispatcher.join()
        self.ssl_socket.close()

    def __del__(self):
        self.logout()
