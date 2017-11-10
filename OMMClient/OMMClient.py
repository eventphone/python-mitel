from threading import Thread, Event, Lock
from time import sleep
from events import Events
from utils import *
from messagehelper import *
import socket
import ssl
import Queue


class OMMClient(Events):
    _host = None
    _port = None
    _tcp_socket = None
    _ssl_socket = None
    _send_q = None
    _recv_q = None
    _worker = None
    _dispatcher = None
    _sequence = 0
    _sequencelock = Lock()
    _terminate = False
    _events = {}
    _eventlock = Lock()
    _modulus = None
    _exponent = None
    _logged_in = False
    omm_status = {}
    omm_versions = {}
    __events__ = ('on_RFPState', 'on_HealthState', 'on_DECTSubscriptionMode', 'on_PPDevCnf')

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.settimeout(10)
        self._ssl_socket = ssl.wrap_socket(self._tcp_socket)
        self._send_q = Queue.Queue()
        self._recv_q = Queue.Queue()
        self._worker = Thread(target=self._work)
        self._worker.daemon = True
        self._dispatcher = Thread(target=self._dispatch)
        self._dispatcher.daemon = True

    def __getattr__(self, name):
        #
        # Check if new property and Named like Eventhandler
        #
        if name not in self.__dict__ and name in self.__events__:
            omm_event = name.split("_")[1]
            self.subscribe_event(omm_event)
        return Events.__getattr__(self, name)

    def _get_sequence(self):
        with self._sequencelock:
            sequence = self._sequence
            self._sequence += 1
        return sequence

    def _awaitresponse(self, message):
        if message in self._events:
            raise Exception("Alread waiting for "+message)
        e = Event()
        with self._eventlock:
            self._events[message] = {}
            self._events[message]["event"] = e
        self._events[message]["event"].wait()
        data = parse_message(self._events[message]["response"])
        with self._eventlock:
            self._events.pop(message)
        return data

    def _sendrequest(self, message, messagedata=None, children=None):
        msg = construct_message(message, messagedata, children)
        self._send_q.put(msg)
        responsemssage = message+"Resp"
        if messagedata is not None and "seq" in messagedata:
            responsemssage += messagedata["seq"]
        return self._awaitresponse(responsemssage)

    def login(self, user, password):
        messagedata = {
            "protocolVersion": "45",
            "username": user,
            "password": password,
            "OMPClient": "1"
        }
        self._ssl_socket.connect((self._host, self._port))
        self._worker.start()
        self._dispatcher.start()
        message, attributes, children = self._sendrequest("Open", messagedata)
        self._modulus = children["publicKey"]["modulus"]
        self._exponent = children["publicKey"]["exponent"]
        self.omm_status = attributes
        self.omm_versions = self.get_versions()
        self._logged_in = True

    def _ensure_login(self):
        if not self._logged_in:
            raise Exception("OMMClient not logged in")

    # Subscribes to any event specified
    def subscribe_event(self, event):
        self._ensure_login()
        self._sendrequest("Subscribe", {}, {"e": {"cmd": "On", "eventType": event}})

    # Fetches the configured SARI
    def get_sari(self):
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetSARI")
        return attributes.get("sari")

    # Fetches the OMM system name
    def get_systemname(self):
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetSystemName")
        return attributes.get("name")

    # Fetches maximum Numbers for RFPs, users ect. Returns a dictionary
    def get_limits(self):
        self._ensure_login()
        message, attributes, children = self._sendrequest("Limits")
        return attributes

    # Fetches the OMM supported protocol versions for all calls. Returns a dictionary
    def get_versions(self):
        message, attributes, children = self._sendrequest("GetVersions")
        return attributes

    # Set DECT Subscription Mode (Modes are: off, configured, wildcard)
    def set_subscription(self, mode, timeout=None):
        modes = {
            "OFF" : "Off",
            "WILDCARD" : "Wildcard",
            "CONFIGURED" : "Configured"
        }
        if mode is None or mode.upper() not in modes:
            return False
        messagedata = {
            "mode": modes[mode.upper()],
        }
        if mode is "Wildcard" and timeout is not None:
            return False
        else:
            messagedata["timeout"] = timeout
        message, attributes, children = self._sendrequest("SetDECTSubscriptionMode", messagedata)
        return True

    def set_user_pin(self, uid, pin):
        messagedata = {
            "user":{
                "uid":uid,
                "pin":encrypt_pin(pin, self._modulus,self._exponent)
            }
        }
        message, attributes, children = self._sendrequest("SetPPUser",{"seq": str(self._get_sequence())}, messagedata)
        if len(children) > 0 and children["user"] is not None:
            return True
        else:
            return False


    # Pings OMM and awaits response
    def ping(self):
        self._ensure_login()
        self._sendrequest("Ping", {})

    # Deletes a configured PP
    def delete_device(self, ppid):
        self._ensure_login()
        self._sendrequest("DeletePPDev", {"ppn": str(ppid), "seq": str(self._get_sequence())})

    # Fetches the current state of a PP
    def get_device_state(self, ppid):
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetPPState",
                                                          {"ppn": str(ppid), "seq": str(self._get_sequence())})
        return attributes

    def _work(self):
        while not self._terminate:
            if not self._send_q.empty():
                item = self._send_q.get(block=False)
                self._ssl_socket.send(item + chr(0))
                self._send_q.task_done()
            self._ssl_socket.settimeout(0.1)
            data = None
            try:
                data = self._ssl_socket.recv(16384)
            except ssl.SSLError, e:
                if e.message == "The read operation timed out":
                    continue
            if data:
                self._recv_q.put(data)

    def _dispatch(self):
        while not self._terminate:
            sleep(0.1)
            if not self._recv_q.empty():
                item = self._recv_q.get(block=False)
                message, attributes, children = parse_message(item)
                if message == "EventDECTSubscriptionMode":
                    self.on_DECTSubscriptionMode(message, attributes, children)
                    continue
                if "seq" in attributes:
                    message += attributes["seq"]
                with self._eventlock:
                    if message in self._events:
                            self._events[message]["response"] = item
                            self._events[message]["event"].set()

    def logout(self):
        self._logged_in = False
        self._terminate = True
        self._worker.join()
        self._dispatcher.join()
        self._ssl_socket.close()

    def __del__(self):
        self.logout()
