from time import sleep

from OMMClient import OMMClient,messagehelper
from testconfig import *
import os
import signal

def SubscriptionHandler(message, attributes, children):
    print("eventhandler: "+message)
    print("attributes: "+attributes.join())

test = OMMClient.OMMClient(host, port)
test.login(user, password)
test.on_DECTSubscriptionMode += SubscriptionHandler
print("SARI: "+test.get_sari())
test.get_device_state(12)
i=0
while i<58:
    i +=1
    #sleep(0.25)
    test.ping()
    print("main loop")
test.delete_device(13)
test.logout()
print("end reached")
