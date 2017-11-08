from OMMClient import OMMClient
test = OMMClient.OMMClient("ipaddress",12622)
test.login("user","password")
while True:
    resp=    test.recv_q.get_nowait()
    if resp is not None:
        print(resp)
        break
