from time import sleep

from OMMClient import OMMClient,messagehelper
from testconfig import *
import os
import signal


test = OMMClient.OMMClient(host, port)
test.login(user, password)
print test.get_sari()
i=0
while i<8:
    i +=1
    sleep(0.25)
    test.ping()
    print("mainloop")
test.logout()
print("end reached")
