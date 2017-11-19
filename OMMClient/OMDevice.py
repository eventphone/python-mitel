from OMMClient import *
from threading import Lock


class OMMDevice:
    """
    :type _ommclient: OMMClient
    :param _ommclient: OMM Client
    :type uid: int
    :param uid: id of the associated user
    :type ppn: int
    :param name: OMM's internal device id
    :type name: str
    :param useSIPUserName: login user to register user to sip registrar
    :type useSIPUserName: str
    :param ppnOld: last device id assigned
    :type ppnOld: int
    """
    ac = None
    uid = None
    timeStampSubscription = None
    ppn = None
    ppnSec = None
    capBluetooth = None
    ppDefaultProfileLoaded = None
    timeStampAdmin = None
    encrypt = None
    ommIdAck = None
    subscribeToPARIOnly = None
    timeStamp = None
    ommId = None
    modicType = None
    subscriptionId = None
    ppProfileCapability = None
    relType = None
    ethAddr = None
    timeStampRelation = None
    timeStampRoaming = None
    capEnhLocating = None
    capMessaging = None
    dectIeFixedId = None
    roaming = None
    autoCreate = None
    ipei = None
    uak = None
    hwType = None
    s = None
    capMessagingForInternalUse = None
    locationData = None
    _ommclient = None
    _changes = None
    _changelock = Lock()

    def __init__(self, ommclient, attributes=None):
        self.__dict__["_ommclient"] = ommclient
        self.__dict__["_changes"] = {}
        if attributes is not None:
            self._init_from_attributes(attributes)

    def __repr__(self):
        return self.ipei

    def __getattr__(self, item):
        return self.__dict__[item.name]

    def __setattr__(self, key, value):
        if key is "ppn" and "ppn" in self.__dict__:
            raise Exception("Cannot change ppn !")
        with self._changelock:
            self._changes[key] = value
            self.__dict__[key] = value

    def _init_from_attributes(self, attributes):
        for key, val in attributes.items():
            self.__dict__[key] = val