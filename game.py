import threading
import tkinter
from tkinter import messagebox
import service

# Ho importato service.py che gestisce configurazione dei socket e creazione della connesione, cosi
# nel caso ci sarà un errore catturato da try-except il programma si chiuderà prima evitando di sprecare più memoria
# per dedicarla alle variabili interessate a creare la finestra del gioco

# Richiamando la funzione che risiede nel service.py restituisco a gui.py gli oggetti dei rispettivi
# socket tcp e udp multicast
tcps, udps = service.connect()


num_b = 10 # Numero massimo di palline nel gioco
# Numero massimo dei giocatori in una partita (Tale caratteristica l'ho gestita e aggiunta anche nel lato server)
num_players = 23
player_names=[] # Lista dedicata alle stringhe dei rispettivi nomi e punti ottenuti dei giocatori
balls = [] # Lista delle palline che permetterà in futuro ad accedere a ogni oggeto oval e spostarla alle sue nuove coordinate 


window = tkinter.Tk()# Creazione della finestra principale del gioco
window.title("ClickerPy")# Imposto il titolo della finestra
window.geometry('740x740')# Configurazione delle dimensioni della finestra
window.configure( background="#111217" )# Configurazione del colore dello sfondo
window.resizable(0, 0)# Aggiungo la restrizione che vieta il cambiamento delle dimensioni della finestra

l_frame = tkinter.Frame( bg="#111217" ) # Creo il primo container che avrà nel suo interno il canvas e la label title_l. L'oggetto Frame serve per gestire la posizione dei widget presenti dentro di lui.
l_frame.pack(side="left") # pack() ci conferma la sua visualizzazione dentro la finestra. Side specifica su quale lato impacchettare il widget.
# Score_frame raccoglierà tutte le label per visualizzazione del punteggio di ciascun giocatore. Ha un titolo che viene specificato nel parametro text. Labelanchor fissa tale titolo in una posizione specificata
# dal programmatore, in questo caso è Nord(cioè Top)
score_frame = tkinter.LabelFrame(window, text="SCORE", bg="#111217", fg="white", highlightbackground="#1d1e23", highlightthickness=5, bd=0, padx=5, pady=5, labelanchor="n")
score_frame.pack(side="right", padx=5, pady=5)

# Creo un oggetto stringa e la metto dentro la label title_l tramite parametro textvariable. Con questo metodo riuscirò, nella funzione labelUpdate di aggiornare costantemente la label title_l attraverso 
# la modifica di di title con il metodo set()
title = tkinter.StringVar()
# L'oggetto/widget Label viene utilizzato per visualizzare un testo o un'immagine sullo schermo.
title_l = tkinter.Label(l_frame, textvariable=title, bg="#2d2d35", fg="white", bd =3, width = 15)
title_l.pack()

# L'oggetto canvas sarà il nostro principale oggetto su cui rappresenteremo le palline inviate dal server attraverso spostamento delle coordinate.
# Questo widget può essere utilizzato per disegnare varie grafiche impostate dal programmatore
canvas = tkinter.Canvas(l_frame, width=500, height=500, bg = '#2d2d35', highlightthickness=5, highlightbackground="#1d1e23")
def callback(event):
	coords = str(event.x)+","+str(event.y)
	tcps.sendall(coords.encode())
# Lego al nostro canvas un listener che intercetterà ogni rilascio(ButtonRelease) del bottone sinistro del mouse e di conseguenza eseguirà la funzione callback
# che invierà le coordinate x e y del mouse in quel istante al server.
canvas.bind('<ButtonRelease-1>', callback) # Ho scelto <ButtonRelease-1> invece del <Button-1> per eliminare la situazione dove il giocatore ha il tasto ancora premuto ma la pallina ha già cambiato la posizione.
canvas.pack(padx = 10, pady=10)

# In un loop che itererà num_players volte creò le rispettive label per visualizzazione del punteggio di ciascun giocatore con la loro StringVar() personale che sarà reperibile tramite la lista player_names
for i in range(num_players):
	p = tkinter.StringVar()
	p.set("")
	player_names.append( p )
	tkinter.Label(score_frame, textvariable=player_names[i], bg="#2d2d35", fg="white", bd =3, width = 25).pack(pady = 3)

# Creo num_b palline poste fuori dal canvas all'esecuzione del codice. Ogni pallina creatà viene aggiunta all lista balls cosi da facilatare, più avanti, la gestione del loro spostamento.
for i in range(num_b):
	balls.append(canvas.create_oval(0-25, 0-25, 0+25, 0+25, activefill="#01C165"))

# labelUpdate itererà ,per ogni elemento in names, un loop for che estrapolerà( .split() ) da ogni elemento n il nome del giocatore e il suo punteggio, aggiornando cosi la label del giocatore.
# Prima di ciò pero la lista names viene ordinata in base al punteggio discendente
def labelUpdate(names):
	title.set("LOBBY - "+str(len(names))+"/"+str(num_players)) #Aggiornamento della stringvar title ci permette di sapere il numero dei giocatori connessi.
	names.sort(key = lambda x: -int(x.split(",")[1]))
	i = 0
	for n in names:
		if n != '':
			name, points = n.split(",",2)
			player_names[i].set(name +": "+ points)
			i += 1

# checkObj itererà ,per ogni elemento in coords, un loop for che estrapolerà( .split() ) da ogni elemento c:
# -la nuova coordinata x della pallina
# -La nuova coordinata y della pallina
# -Il nuovo colore da impostare alla pallina
# -Il raggio(serve per creare l'illusione della pulsazione delle palline)
def checkObj(coords):
	i = 0
	for c in coords:
		if c != '':
			x,y,fill,r = c.split(",",4)
			x = int(x)
			y = int(y)
			r = int(r)
			canvas.coords(balls[i],x-r,y-r,x+r,y+r)
			canvas.itemconfig(balls[i],fill=fill)
			i += 1

# Creò un thread che eseguirà in loop la funzione objUpdate.
# Nella funzione, tramite try, il client prova a ricevere dei messaggi attraverso il socket udps impostato in multicast.
# Dopo aver ricevuto il pacchetto data, faccio il decode() dei byte ricevuti cosi da restituire una stringa.
# Divido la stringa, per ogni carattere ":", in due(in questo caso so che ci sarà solo un ":" , di coseguenza mi restituirà solo due stringhe) e la salvo in una lista data
# Ciascuna elemento della lista, data[0] contenente le nuove coordinate delle palline e data[1] contenente i nomi dei giocatori e i loro punteggi, lo passo, gia diviso per ogni ";" per creare le liste
# names e coords, come paramentro per ciascuna delle funzioni.
def objUpdate(udps):
	while True:
		try:
			data, addr = udps.recvfrom(1024)
			data = data.decode()
			data = data.split(":",2)
			checkObj(data[0].split(";"))
			labelUpdate(data[1].split(";"))
		except:
			break
threading.Thread(target=objUpdate,args = (udps,)).start()

# Con window.protocol("WM_DELETE_WINDOW", on_closing) imposto delle azioni da eseguire, dopo aver premuto il bottone x della finestra, ovvero:
# creo un box di messagio a pop up che avrà titolo "Quit" e un testo all'interno "Do you want to quit?". Se il return del box sarà True invio al server 
# il messagio di disconnesione ciudo tutti i socket e distruggo la finetra
def on_closing():
	if messagebox.askokcancel("Quit", "Do you want to quit?"):
		tcps.sendall(b"close_connection")
		udps.close()
		tcps.close()
		window.destroy()
window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()
