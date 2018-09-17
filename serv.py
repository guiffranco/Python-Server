import socket
import datetime

# cria um socket usando o protocolo IPV4 e conexão TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "127.0.0.1"
port = 7000

# mensagem para quando se conectar
msg = b"Hey, this is a msg from serv to cli. Your msg has arrived."

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
		buff_size = 4
		print("Waiting for a ", buff_size, "bytes string having client msg size")
		data_lenght = con.recv(buff_size)
		print("Data lenght received:", data_lenght.decode("ascii"))
		realData = con.recv(int(data_lenght))
		print("Real data received:", realData.decode("ascii"))
		if realData:
			print("Sendind data to client...")
			con.send(msg)
			print("Done!")
	finally:
		# fecha a conexão
		print("Closing", add, "socket...")
		con.close()
	print("I'm not dead... I'll keep listening...")
