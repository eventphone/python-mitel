from time import sleep

from OMMClient import OMMClient,messagehelper
from testconfig import *
import os
import signal


test = OMMClient.OMMClient(host, port)
print test.login(user, password)
i=0
while i<8:
    i +=1
    sleep(0.25)
    print("mainloop")
test.logout()
print("end reached")
