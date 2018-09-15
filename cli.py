import socket

# cria um socket usando o protocolo IPV4 e conexão TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "" #127.0.0.1
port = 7000

msg = "msg from cli to serv"

# conecta com o servidor
s.connect((host, port))

try:
    print('Sendind message...')
    s.sendall(msg.encode('ascii'))

    # aguardando a resposta
    amount_recv = 0
    amount_expc = len(msg)
    # passa 1024 bytes pela rede
    while amount_recv < amount_expc:
        data = s.recv(100)
        amount_recv += len(data)
        # mostrar dados
        print('Data received: ', data.decode("ascii"))
        print('Data size: ', amount_recv)

finally:
    print('Closing socket...')
    s.close()
