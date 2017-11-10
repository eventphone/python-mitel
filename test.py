from time import sleep
from OMMClient import OMMClient,messagehelper
from OMMClient.utils import convert_ipui
from testconfig import *
import os
import signal

def SubscriptionHandler(message, attributes, children):
    print("eventhandler: "+message)
    print("Mode: "+attributes["mode"])

def HandsetHandler(message, attributes, children):
    print("eventhandler: "+message)
    #print("Mode: "+attributes["mode"])

test = OMMClient.OMMClient(host, port)
test.login(user, password)
test.on_DECTSubscriptionMode += SubscriptionHandler
test.on_PPDevCnf += HandsetHandler
print("SARI: "+test.get_sari())
print("OMM: "+test.get_systemname())
print(test.get_limits())
print(test.set_subscription("Off"))
print(test.set_user_pin(55,"1234"))
test.get_device_state(12)
i=0
while i<120:
    i +=1
    sleep(0.5)
    test.ping()
    print("main loop")
test.delete_device(13)
test.logout()
print("end reached")
