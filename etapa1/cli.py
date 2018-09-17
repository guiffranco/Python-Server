import socket
import datetime

# cria um socket usando o protocolo IPV4 e conexão TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "" # 127.0.0.1
port = 7000

server_buff_size = 8

print("Escolha entre\n1 - Digitar sua própria mensagem\n2 - Ler uma mensagem a partir de um arquivo externo")
op = input()
if(op == "1"):
    print("Digite uma mensagem para enviar ao servidor:")
    msg = input()
elif(op == "2"):
    print("Digite o nome do arquivo:")
    file_name = input()
    file = open(file_name+".txt", "r")
    msg = file.read()

# conecta com o servidor
s.connect((host, port))

try:
    print("--------------------------")
    print(datetime.datetime.now())
    msg_lenght = str(len(msg)).ljust(server_buff_size)[:server_buff_size]
    print("Sendind message size:", msg_lenght)
    s.sendall(msg_lenght.encode("ascii"))
    print("Sendind real message...")
    s.sendall(msg.encode("ascii"))
    # aguardando a resposta
    data = s.recv(1024)
    # mostrar dados
    print("Data received:", data.decode("ascii"))
    print("Data size:", len(data), "bytes")
finally:
    print("Closing socket...")
    s.close()
