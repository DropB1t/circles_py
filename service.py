import socket
import struct

# Funzione send_names chiede al utente tramite l'input il suo nome da inviare al server
def send_name():
	while True:
		name = input('Please enter your nickname (maximum 20 characters) --> ')
		if len(name) > 0 and len(name) < 21:
			return name.encode('utf-8')

def connect():
    ip = input("Enter the server ip--> ")
    port = 1235
 
    multicast_group = '225.1.1.1'
    multicast_port  = 5007

    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
    udps.bind(('', multicast_port ))
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    udps.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    tcps = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    try:
        tcps.connect( (ip,port) )
        tcps.sendall( send_name() )
    except:
        print("Connection cannot be established!")
        quit()

    return tcps, udps