from OMMClient import *
from threading import Lock


class OMMUser:
    """
    :type _ommclient: OMMClient
    :param _ommclient: OMM Client
    :type uid: int
    :param uid: OMM's internal user id
    :type ppn: int
    :param name: user name
    :type name: str
    :param useSIPUserName: login user to register user to sip registrar
    :type useSIPUserName: str
    :param ppnOld: last device id assigned
    :type ppnOld: int
    """
    msgRight = None
    uid = None
    pin = None
    recvVcardRight = None
    ppn = None
    useSIPUserAuthentication = None
    trackingActive = None
    autoAnswer = None
    BTsensitivity = None
    num = None
    sendVcardRight = None
    warningTone = None
    SWS = None
    HBS = None
    keepLocalPB = None
    timeStampAdmin = None
    holdRingBackTime = None
    forwardState = None
    sipAuthId = None
    timeStamp = None
    ppnOld = None
    addId = None
    HSS = None
    permanent = None
    forwardDest = None
    allowVideoStream = None
    sipRegisterCheck = None
    ppProfileId = None
    relType = None
    SCS = None
    serviceAuthName = None
    HCS = None
    hotDeskingSupport = None
    CUS = None
    callWaitingDisabled = None
    calculatedSipPort = None
    manDownNum = None
    CDS = None
    voiceboxNum = None
    timeStampRelation = None
    HRS = None
    SRS = None
    allowBargeIn = None
    external = None
    uidSec = None
    HAS = None
    conferenceServerURI = None
    conferenceServerType = None
    lang = None
    useSIPUserName = None
    sipPw = None
    fixedSipPort = None
    name = None
    BTS = None
    credentialPw = None
    locRight = None
    locatable = None
    vip = None
    configurationDataLoaded = None
    sosNum = None
    autoLogoutOnCharge = None
    serviceAuthPassword = None
    monitoringMode = None
    microphoneMute = None
    hierarchy1 = None
    hierarchy2 = None
    BTlocatable = None
    serviceUserName = None
    forwardTime = None
    _ommclient = None
    _changes = None
    _changelock = Lock()

    def __init__(self, ommclient, attributes=None):
        self.__dict__["_ommclient"] = ommclient
        self.__dict__["_changes"] = {}
        if attributes is not None:
            self._init_from_attributes(attributes)

    def __getattr__(self, item):
        return self.__dict__[item]

    def __setattr__(self, key, value):
        if key is "uid" and "uid" in self.__dict__:
            raise Exception("Cannot change uid !")
        with self._changelock:
            self._changes[key] = value
            self.__dict__[key] = value

    def _init_from_attributes(self, attributes):
        for key, val in attributes.items():
            self.__dict__[key] = val

    def get_attributes(self):
        attributes = {}
        for key, val in self.__dict__.items():
            if "_" in key:
                attributes[key] = val
        return attributes

    def commit(self):
        if len(self._changes) == 0:
            return True
        with self._changelock:
            for change in self._changes:
                print change
