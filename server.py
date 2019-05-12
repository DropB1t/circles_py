import socket
import time
from threading import Lock, Thread
import random
import math

def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP

#TCP
port = 1235
ip = get_ip()
serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind( (ip,port) )
serverSocket.listen(1000)

#UDP Multicast
MCAST_GRP = '225.1.1.1'
MCAST_PORT = 5007
MULTICAST_TTL = 2
multiSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
multiSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

Finish = False # Boolean che determina l'uscita dei thread dal loop while True quando l'esecuzione del server finisce.
lock = Lock() # L'oggetto lock per sincronizzare la concorrenza tra i thread

raggio = 25
palle=[]
colors = ["#D80032","#0075F2","#6320EE","#F2DA43"] #La lista con i colori delle palline

num_players = 23 # Numero massimo di giocatori in una partita
clients = []


for i in range(10):
	palle.append( [random.randint(10, 500),random.randint(10, 500), random.choice(colors), raggio] ) # Nell'append dei attributi di ogni palla ho aggiunto anche il colore(che viene scelto random con .choice()) e il raggio

def distanza(p1,p2):
	return math.sqrt( math.pow(p1[0]-p2[0],2) + math.pow(p1[1]-p2[1],2))


class Client(Thread):

	def __init__(self,sock,ip):
		super(Client,self).__init__()
		self.ip=ip[0]
		self.sock=sock
		self.name=""
		self.p=0

	def run(self):
		self.name = self.sock.recv(1024).decode()
		print(self.name+" has connected with "+self.ip)
		while True:
			if Finish:
				break
			msg=self.sock.recv(1024).decode()
			if msg !="close_connection":
				c = [int(sc) for sc in msg.split(",")]
				npr=0
				# Il Thread acquisce l'accesso a tutte le variabili tra .acquire() e release() e blocca tutti gli altri thread alla loro modifica(Serve principalmente a bloccare la funzione evolvi() di cambiare
				# il raggio mentre vengo eseguiti i calcoli della distanza e l'append() di una palla)
				lock.acquire() 
				for p in palle:
					if distanza(p,c)<raggio:	
						palle.remove(p)
						npr=npr+1
				self.p=self.p+npr
				for i in range(npr):
					palle.append( [random.randint(10, 500),random.randint(10, 500), random.choice(colors), raggio])
				lock.release()
			else:
				print(self.name+" has disconnected")
				clients.remove(self)
				break

	def toString(self):
		return self.name+","+str(self.p)

# La nuova funzione evolvi cambia costantemente la grandezza del raggio tra 30 e 25
def evolvi():
	global raggio
	Expand = True
	while True:
		if Finish:
			break
		time.sleep(0.1)
		if Expand:
			raggio += 1
		else:
			raggio -= 1
		if raggio == 30 or raggio == 25:
			Expand = not Expand
Thread(target=evolvi,args=()).start()

def generaStringa():
	msg=";".join( [ str(x[0])+","+str(x[1])+","+str(x[2])+","+str(raggio) for x in palle ] ) # nel join dei valori da inviare ho aggiunto il colore di ogni palla presente nella lista e il raggio
	msg = msg+":"+";".join([c.toString() for c in clients])
	return msg

def accettaClient():
	while True:
		if Finish:
			break
		if len(clients) < num_players: # Se la lunghezza della lista clients è maggiore o uguale a num_players non vengono più accettati nuove connessioni con il server da aprte dei client
			cs,cip = serverSocket.accept()
			client=Client(cs,cip)
			client.start()
			clients.append( client )
Thread(target=accettaClient,args=()).start()

try:
	while True:
		time.sleep(0.1)
		s=generaStringa()
		multiSock.sendto(s.encode(), (MCAST_GRP, MCAST_PORT))
except (KeyboardInterrupt, SystemExit):
	Finish = True