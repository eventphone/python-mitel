# python-mitel (Python API for Mitel SIP-DECT)

## Overview and Purpose

The Mitel SIP-DECT solution is a scalable IP-based multicell
DECT-System. Multiple DECT basestations (RFPs) can be used to extend
coverage. Up to 10.000 handsets (PPs) can be registered to use the
system. All RFPs are orchestrated by one central component. It is
called Open Mobility Manager (OMM). RFPs and PPs can be configured
using a web based GUI as well as a java client application. The java
client application called OMP connects to OMM using a custom xml-based
protocol over an SSL-socket. The idea behind this Python Module is
to reverse-engenieer that protocol to be able to script all changes
inside the OMM.

This library has been replaced by https://github.com/eventphone/mitel-api and is no longer actively maintained.

## Documentation
[![Documentation Status](https://readthedocs.org/projects/python-mitel/badge/?version=latest)](http://python-mitel.readthedocs.io/en/latest/?badge=latest)

Documentation can be found here:
http://python-mitel.readthedocs.io/.

## References
After reverse engineering the api interface between OMP and OMM google
came up with a vendor api documentation which can be found here:

[SIP-DECT OM Application XML Interface OMM V 6.1](http://www.voipinfo.net/docs/mitel/aad-0384_OM_AXI_OM_Rel_6.1.pdf)


## Following features are targeted:
- Configure subscription mode (Off, Subscription, Wildcard) ✅
- Handle subscription mode change ✅
- Create new user profiles ✅
- Create new devices (PPs) using known IPEI/IPUI
- Attach existing profiles to devices ✅
- Detach a user profile from a device ✅
- Reset a user's PIN to move a dynamic profile ✅

## Use cases:
- Build a custom yate-script to login a user profile to a PP
- Keep the system in wildcard registration mode
- Synchronisation of user profiles from external data source

## Implemented Features:
### System-Wide
- Subscribe to defined OMM-Events
- Send a PING request to OMM
- Get System Name
- Get System SARI
- Get System Limits (Maximum Values)
- Get Protocol Versions per OMM-call
- Set DECT Subscription-Mode
- Get OMM User Account by ID
- Login Default and Login as OMM-Sync

### Users (User Profiles)
- Create new user profile
- Get User by ID
- Reset User-PIN
- Attach User to Device
- Detach User from Device
- Convert User-Device Relation to Fixed
- Convert User-Device Relation to Dynamic

### Devices (Protable Parts)
- Delete Device (PP)
- Get Device State

## Usage example:
The following example logs into OMM and executes some operations.
It also handles the event of a subscription mode change.

```python
# Implement Event Handler for subcription mode change
def SubscriptionHandler(message, attributes, children):
    print("Subscription Mode changed!")
    print("New mode: "+attributes["mode"])

# Login to OMM
test = OMMClient.OMMClient("<omm host>", 12622)
test.login("omm", "<super secure password>")

# Attach Event Handler
test.on_DECTSubscriptionMode += SubscriptionHandler

# Get some Basic Infos
print("SARI: "+test.get_sari())
print("OMM: "+test.get_systemname())
print(test.get_limits())

# Disable DECT registration
print(test.set_subscription("Off"))

# Reset the PIN of User number 55 to 1234
print(test.set_user_pin(55,"1234"))

# Ping OMM 5 times
while i<5:
    i +=1
    sleep(0.5)
    test.ping()

#Close OMM connection
test.logout()
```
