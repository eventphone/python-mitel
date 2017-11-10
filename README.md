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

## Following features are targeted:
- Configure subscription mode (Off, Subscription, Wildcard) ✅
- Handle subscription mode change ✅
- Create new user profiles
- Create new devices (PPs) using known IPEI/IPUI
- Attach existing profiles to devices
- Detach a user profile from a device
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

### Users (User Profiles)
- Reset User-PIN

### Devices (Protable Parts)
- Delete Device (PP)
- Get Device State