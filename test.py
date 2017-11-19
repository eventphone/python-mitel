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
test.login(user, password, ommsync=True)
#print test.get_device(32)
#print test.create_user("test1","3332",login="3332",pin="1234")
user = test.get_user(1)
user.update()
print user.name
print user.pin
#test.attach_user_device(1, 36)
#test.detach_user_device(5, 35)

test.on_DECTSubscriptionMode += SubscriptionHandler
test.on_PPDevCnf += HandsetHandler
print("SARI: "+test.get_sari())
print("OMM: "+test.get_systemname())
#print(test.set_user_pin(55,"1234"))
test.get_device_state(12)
i=0
while i<2:
    i +=1
    sleep(0.5)
    test.ping()
test.logout()
print("end reached")
