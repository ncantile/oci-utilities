tunnelNames = ["IPSec-Tunnel1", "IPSec-Tunnel2"]
cpeIP = '10.10.10.10'
ikeVer = 'IKEv2'
routingType = 'POLICY'
tunnelSecret = 'eifeiafhidkafiwejs7384u83rfhuehd8iuu82u92hdi'
tunnelNamesAndIP = {'IPSec-Tunnel2': '193.122.0.91', 'IPSec-Tunnel1': '158.101.179.221'}
insideIP = ['1.1.1.1', '2.2.2.2']
outsideIP = []

print ('Below you can find the configuration file. Please provide this file to the networking team entrusted with configuring the actual Customer-Premises equipment.')
print ('|-------------------|--------------------------------------------------------------------------------|')
print(f'| {"CPE IP": <30} | {cpeIP: <70}|')
print(f'| {"IKE version": <30} | {ikeVer: <70}|')
print(f'| {"Routing Type": <30} | {routingType.replace("POLICY","STATIC"): <70}|')
print(f'| {"Shared Secret": <30} | {tunnelSecret: <70}|')
for tun in tunnelNames:
    print(f'| {tun: <100}|')
    print(f'| {"Tunnel IP endpoint": <30} | {tunnelNamesAndIP[tun]: <70}|')
    if len(insideIP) > 0:
        print(f'| {"Oracle interface IP": <30} | {insideIP[tunnelIndex]: <70}|')
    if len(outsideIP) > 0:
        print(f'| {"CPE interface IP": <30} | {outsideIP[tunnelIndex]: <70}|')
    print(f'| {"Phase 1 info": <30} | {" ": <70}|')
    print(f'| {"  Authentication algorithm": <30} | {"SHA2-384": <70}|')
    print(f'| {"  Encryption algorithm": <30} | {"AES-256-CBC": <70}|')
    print(f'| {"  DH Group": <30} | {"group 20 (ECP 384-bit random)": <70}|')
    print(f'| {"  IKE lifetime": <30} | {"28800 seconds (8 hours)": <70}|')
    print(f'| {"Phase 2 info": <30} | {" ": <70}|')
    print(f'| {"  Authentication algorithm": <30} | {"HMAC-SHA-256-128": <70}|')
    print(f'| {"  Encryption algorithm": <30} | {"AES-256-GCM": <70}|')
    print(f'| {"  Perfect-forward secrecy": <30} | {"Enabled": <70}|')
    print(f'| {"  DH Group": <30} | {"group 5 (MODP 1536-bit)": <70}|')
    print(f'| {"  IPSec lifetime": <30} | {"3600 seconds (1 hour)": <70}|')
print ('======================================================================================================')
