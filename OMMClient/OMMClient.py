from threading import Thread, Event, Lock
from OMUser import OMMUser
from time import sleep
from events import Events
from utils import *
from messagehelper import *
import socket
import ssl
import Queue


# noinspection PyMissingConstructor
class OMMClient(Events):
    """
    """
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

    def __init__(self, host, port=12622):
        """ Initializes a new OMM Client using destination address and port

        Args:
            host (str): address of the server running OMM
            port (int): port the OMM service is listening
        """
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
        """ Check if new property and Named like Eventhandler

        Args:
            name:

        Returns:

        """
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
            raise Exception("Already waiting for "+message)
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
        """

        Args:
            message:
            messagedata:
            children:

        Returns:

        """
        msg = construct_message(message, messagedata, children)
        self._send_q.put(msg)
        responsemssage = message+"Resp"
        if messagedata is not None and "seq" in messagedata:
            responsemssage += str(messagedata["seq"])
        return self._awaitresponse(responsemssage)

    def login(self, user, password, ommsync=False):
        """ login to OMM with given credentials

        Method used to login before executing any command except get_versions
        against the OMM. The login can be performed in two modes to support
        different sets of features. The normal OMPClient login is restricted
        to all operations which can be performed using the OMP client application.
        Using the OMM sync flag you will be able to perform further operations.
        These operations are:

            * Attach user profile to device (Login)
            * Detach user profile from device (Logout)
            * Write extended device information (read only in OMP)

        .. note:: Some operations in OMM-Sync mode might lead to destroy DECT paring.

        Args:
            user (str): Username to be used to login
            password (str): Password to be used to login
            ommsync (bool): If True login as OMM-Sync client
        """
        messagedata = {
            "protocolVersion": "45",
            "username": user,
            "password": password
        }
        if ommsync is True:
            messagedata["UserDeviceSyncClient"] = "true"
        else:
            messagedata["OMPClient"] = "1"
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

    def get_account(self, uid):
        """ Get System Account

        Args:
            uid:
        """
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetAccount", {"id": uid})
        return attributes

    def subscribe_event(self, event):
        """ Subscribes to any event specified

        Args:
            event:
        """
        self._ensure_login()
        self._sendrequest("Subscribe", {}, {"e": {"cmd": "On", "eventType": event}})

    def get_sari(self):
        """ Fetches the configured SARI

        Returns:
            Configured SARI for the OMM system

        """
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetSARI")
        return attributes.get("sari")

    def get_systemname(self):
        """ Fetches the OMM system name

        Returns:
            The OMMs configured system name.
        """
        self._ensure_login()
        message, attributes, children = self._sendrequest("GetSystemName")
        return attributes.get("name")

    def get_limits(self):
        """ Fetches maximum Numbers for RFPs, users ect.

        Returns:
            A dict containing all limitations for the different types.
        """
        self._ensure_login()
        message, attributes, children = self._sendrequest("Limits")
        return attributes

    def get_versions(self):
        """ Fetches the OMM supported protocol versions for all calls.

        Returns:
            A dict containing protocol versions for all available calls.

        """
        message, attributes, children = self._sendrequest("GetVersions")
        return attributes

    def set_subscription(self, mode, timeout=None):
        """ Set DECT Subscription Mode (Modes are: off, configured, wildcard)

        Args:
            mode (str): one of the following Modes:
                * off
                * configured
                * wildcard
            timeout (int): The time after that the wildcard mode disables.
                It is only required if switching to wildcard mode.

        Returns:
            True: if parameters are ok
            False: if the parameters are faulty

        """
        modes = {
            "OFF": "Off",
            "WILDCARD": "Wildcard",
            "CONFIGURED": "Configured"
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
        self._sendrequest("SetDECTSubscriptionMode", messagedata)
        return True

    def set_user_pin(self, uid, pin):
        """ rest a user profiles PIN

        Resets the PIN a user uses to login his user profile into a DECT device.
        That can be done by using the defined system feature code, the profiles
        login and this PIN.

        Args:
            uid (int): user profile id
            pin (str): PIN to set

        Returns:
            True: if successful
            False: if the request failed
        """
        messagedata = {
            "user": {
                "uid": uid,
                "pin": encrypt_pin(pin, self._modulus, self._exponent)
            }
        }
        message, attributes, children = self._sendrequest("SetPPUser", {"seq": str(self._get_sequence())}, messagedata)
        if len(children) > 0 and children["user"] is not None:
            return True
        else:
            return False

    def get_device(self,  ppn):
        """ get device configuration data

        Args:
            ppn:

        Returns:

        """
        message, attributes, children = self._sendrequest("GetPPDev", {"seq": self._get_sequence(), "ppn": ppn})
        if children is not None and "pp" in children and children["pp"] is not None \
                and children["pp"]["ppn"] == str(ppn):
            return children["pp"]
        else:
            return None

    def get_user(self,  uid):
        """ get user configuration data

        Obtain the user profiles configuration data like sip-login ect. using the user id.

        Args:
            uid (int): user profile id

        Returns:
            Will return the users profile if the request ist successful.
            If it fails None will be returned.
        """
        message, attributes, children = self._sendrequest("GetPPUser", {"seq": self._get_sequence(), "uid": uid})
        if children is not None and "user" in children and children["user"] is not None \
                and children["user"]["uid"] == str(uid):
            user = OMMUser(self, children["user"])
            return user
        else:
            return None

    def set_user_relation_dynamic(self, uid):
        """ Convert a fixed device-user relation into a dynamic one

        After converting the relation from fixed to dynamic users are able to
        logout the profile from a device using the DECT feature code.

        Args:
            uid (int): user profile id

        Returns:
            Will return the user profile's attributes if successful
            False will be returned if the request failed.
        """
        messagedata = {
            "seq": self._get_sequence(),
            "uid": uid,
            "relType": "Dynamic"
        }
        message, attributes, children = self._sendrequest("SetPPUserDevRelation", messagedata)
        if attributes is not None:
            return attributes
        else:
            return False

    def set_user_relation_fixed(self, uid):
        """ Convert a user-device relation into fixed type

        .. note::
            Prior to this operation the user profile must be bound to a device.

        When a user profile is already logged in (bound) to a device using dynamic
        relationship this method can be used to fix the binding. After that no
        login and logout method can be performed using the DECT mechanisms.

        Args:
            uid (int): user profile id

        Returns:
            If successful it will return a dict containing all information about the user profile.
            Will return False if the request didn't succeed properly.
        """
        messagedata = {
            "seq": self._get_sequence(),
            "uid": uid,
            "relType": "Fixed"
        }
        message, attributes, children = self._sendrequest("SetPPUserDevRelation", messagedata)
        if attributes is not None:
            return attributes
        else:
            return False

    def detach_user_device(self, uid, ppn):
        """ detaches an user profile from an existing device

        .. note::
            You have to obtain the device id also named ppn and the users id named uid.

        Can be used to logout a user profile from a device entry.
        The user can be logged in to another device after that.
        The device can be used to login another user.

        Args:
            uid (int): user profile id
            ppn (int): registered device id

        Returns:
            True if the operation was successful. False if it failed.
        """
        if (type(uid) is not int or type(ppn) is not int) or (ppn <= 0 or uid <= 0):
            return False
        messagedata = {
            "pp": {
                "uid": 0,
                "relType": "Unbound",
                "ppn": ppn
            },
            "user": {
                "uid": uid,
                "relType": "Unbound",
                "ppn": 0
            }
        }
        message, attributes, children = self._sendrequest("SetPP", {"seq": self._get_sequence()}, messagedata)
        if children is not None and "pp" in children and children["pp"]["uid"] == str(uid):
            return True
        else:
            return False

    def attach_user_device(self, uid, ppn):
        """ Connects an existing user profile to an existing subscribed device

        Args:
            uid (int): user profile id
            ppn (int): registered device id

        Returns:
            True if the operation was successful. False if it failed.
        """
        if (type(uid) is not int or type(ppn) is not int) or (ppn <= 0 or uid <= 0):
            return False
        messagedata = {
            "pp": {
                "uid": uid,
                "relType": "Dynamic",
                "ppn": ppn
            },
            "user": {
                "uid": uid,
                "relType": "Dynamic",
                "ppn": ppn
            }
        }
        message, attributes, children = self._sendrequest("SetPP", {"seq": self._get_sequence()}, messagedata)
        if children is not None and "pp" in children and children["pp"]["uid"] == str(uid):
            return True
        else:
            return False

    def ping(self):
        """ Pings OMM and awaits response

        """
        self._ensure_login()
        self._sendrequest("Ping", {})

    def create_user(self, name, number, desc1=None, desc2=None, login=None, pin="", sip_user=None, sip_password=None):
        """ Creates new user

        This function will create a new user profile without a device relation ship in dynamic mode.
        It can be used to loing from a device using the feature access code with login and PIN specified.
        The Feature access code can be configured using OMM. Could be someting like (*1)(4711)(3333).
        Within the example *1 stands for general feature access prefix 4711 is the code for user login.
        And 3333 is the extension for which login is requested. User will be prompted for a PIN.

        .. note:: If no sip user name and sip password is specified number will be used

        :param name: Name for the user profile (Shown as Name in OMP)
        :type name: str
        :param number: number for the user profile (Shown as Number/SIP user name in OMM)
        :type number: str
        :param desc1: Description 1 for the new user profile. Can by any string.
        :type desc1: str
        :param desc2: Description 2 for the new user profile. Can by any string.
        :type desc2: str
        :param login: Login for the use to be used for profile login from DECT or additional ID.
        :type login: str
        :param pin: PIN for profile login via DECT. Any non numeric value doesn't make sense.
        :type pin: str
        :param sip_user: Username for OMM to register the profile against the configured sip registrar
        :type sip_user: str
        :param sip_password: Password for sip register against registrar configured
        :type sip_password: str
        :rtype: dict
        :return: Will return a dict containing data of the new user object if successful. Will return None if it failed.
        """
        children = {
            "user": {
                "name": name,
                "num": number
            }
        }
        if desc1:
            children["user"]["hierarchy1"] = desc1
        if desc2:
            children["user"]["hierarchy2"] = desc2
        if login:
            children["user"]["addId"] = login
        if pin:
            children["user"]["pin"] = encrypt_pin(pin, self._modulus, self._exponent)
        if sip_user:
            children["user"]["sipAuthId"] = sip_user
        if sip_password:
            children["user"]["sipPw"] = encrypt_pin(sip_password, self._modulus, self._exponent)
        message, attributes, children = self._sendrequest("CreatePPUser", {"seq": self._get_sequence()}, children)
        if children is not None and "user" in children:
            return children["user"]
        else:
            return None

    def delete_device(self, ppid):
        """ Delete a configured handset (pp)

        .. note:: This operation can not be undone!

        :param ppid: id of the PP to be deleted (>0)
        :type ppid: int
        :return: None
        """
        self._ensure_login()
        self._sendrequest("DeletePPDev", {"ppn": str(ppid), "seq": str(self._get_sequence())})

    def get_device_state(self, ppid):
        """ Fetches the current state of a PP

        Args:
            :param ppid: id of the PP to get the current state for
            :type ppid: int

        Returns:
            :return: A dict containing the devices state information

        """
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
                data = self._ssl_socket.recv(65536)
            except Exception, e:
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
        """ Logout from OMM

        Calling this method will log you out and close the underlying tcp/ssl socket.
        Login can be called any time to reuse the client object for further calls.

        """
        self._logged_in = False
        self._terminate = True
        self._worker.join()
        self._dispatcher.join()
        self._ssl_socket.close()

    def __del__(self):
        self.logout()
