import socket
import datetime

# cria um socket usando o protocolo IPV4 e conexão TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "127.0.0.1"
port = 7000

# mensagem para quando se conectar
msg = b"hey, this is a msg from serv to cli"

# ativar o servidor/servidor em escuta
s.bind((host, port))
s.listen(10)

# deixar o servidor escutando a todo momento
while True:
	# espera a conexão
	con, add = s.accept()
	try:
		print("--------------------------")
		print(datetime.datetime.now())
		print("Client connected:", add)
		buff_size = 1024
		data = con.recv(buff_size)
		print("I can only handle", buff_size, "bytes")
		print("Data received:", data.decode("ascii"))
		print("Data size:", len(data), "bytes")
		if data:
			print("Sendind data to client...")
			con.send(msg)
			print("Done!")
		else:
			print("No more data from", add)
			break
	finally:
		# fecha a conexão
		print("Closing my client socket...")
		con.close()
	print("I'm not dead... I'll keep listening...")
