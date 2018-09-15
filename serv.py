import socket

# cria um socket usando o protocolo IPV4 e conexão TCP

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "127.0.0.1"
port = 7000

# mensagem para quando se conectar

msg = b"this is a msg from serv to cli"

# ativar o servidor/servidor em escuta

s.bind((host, port))
s.listen(10)

# deixar o servidor escutando a todo momento

while True:
	# espera a conexão
	con, add = s.accept()
	try:
		print("-------------------------")
		print("Conectado com ", add)

		data = con.recv(100)
		print('Data received: ', data.decode("ascii"))
		print('Data size: ', len(data))
		if data:
			print('Sendind data to client...')
			con.send(msg)
			con.close()
		else:
			print("No more data from ", add)
			break
	finally:
		con.close() # fecha a conexão
