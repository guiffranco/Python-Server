import socket
import asyncio
import struct
import time


ETH_P_IP = 0x0800

Pacotes = {}

# Coloque aqui o endereço de destino para onde você quer mandar o ping
dest_addr = '192.168.15.1' # ip do meu router

class Package:
    def __init__(self):
        self.offsets = set()
        self.timer = None
        self.buffer = bytearray()
        self.data_length = 0
        self.total_data_length = None

# Checa de tempos em tempos se já se passaram
# 15 segundos desde que o pacote começou a ser
# recebido
def check_timeouts():
    excluir_por_timeout = []
    for id_pacote in Pacotes:
        if time.time() - Pacotes[id_pacote].timer > 15:
            excluir_por_timeout.append(id_pacote)
    for id_pacote in excluir_por_timeout:
        del Pacotes[id_pacote]
    asyncio.get_event_loop().call_later(1,check_timeouts)

def addr2str(addr):
    return '%d.%d.%d.%d' % tuple(int(x) for x in addr)

def handle_ipv4_header(packet):
    version = packet[0] >> 4
    ihl = packet[0] & 0xf
    assert version == 4
    identification = packet[4:6]
    flags = packet[6] >> 5
    fragment_offset = (int.from_bytes(packet[6:8],byteorder='big',signed=False) & 0x1FFF) * 8
    src_addr = addr2str(packet[12:16])
    segment = packet[4*ihl:]
    return identification, flags, fragment_offset, src_addr, segment

def send_ping(send_fd):
    print('enviando ping')
    # Exemplo de pacote ping (ICMP echo request) com payload grande
    msg = bytearray(b"\x08\x00\x00\x00" + 5000*b"\xba\xdc\x0f\xfe")
    msg[2:4] = struct.pack('!H', calc_checksum(msg))
    send_fd.sendto(msg, (dest_addr, 0))

    asyncio.get_event_loop().call_later(1, send_ping, send_fd)


def raw_recv(recv_fd):
    packet = recv_fd.recv(12000)
    identification, flags, fragment_offset, src_addr, segment = handle_ipv4_header(packet)
    
    
    if(src_addr != dest_addr):
        return

    print('recebido pacote de %d bytes' % len(packet))

    # Caso seja o primeiro fragmento do datagrama criar
    # uma instancia de package e começar a contabilizar
    # o tempo
    if(identification not in Pacotes):
        Pacotes[identification] = pacote = Package()
        pacote.timer = time.time()
    else:
        pacote = Pacotes[identification]

    #evita fragmentos repetidos
    if fragment_offset not in pacote.offsets:
        
        # Caso seja o último fragmento já sabemos
        # o total length do pacote
        if(flags & 0x1 == 0):
            pacote.total_data_length = fragment_offset + len(segment) 
        
        pacote.data_length += len(segment)
        pacote.offsets.add(fragment_offset)
        
        #preenche os espaços faltantes do array com '0' (e os que vão ser adicionados também)
        while len(pacote.buffer) < fragment_offset + len(segment):
            pacote.buffer.append(0)
        
        pacote.buffer[fragment_offset:fragment_offset+len(segment)] = segment

        # Caso ja montou o datagrama, ou caso já tenha vindo
        # completo, imprime informações sobre ele
        if pacote.total_data_length == pacote.data_length:
            print('\tFonte: ', src_addr)
            print('\tIdentificador: ', identification)
            print('\tTamanho dos dados: ', pacote.data_length)
            print('\tConteúdo: ',segment)
            print()


def calc_checksum(segment):
    if len(segment) % 2 == 1:
        # se for ímpar, faz padding à direita
        segment += b'\x00'
    checksum = 0
    for i in range(0, len(segment), 2):
        x, = struct.unpack('!H', segment[i:i+2])
        checksum += x
        while checksum > 0xffff:
            checksum = (checksum & 0xffff) + 1
    checksum = ~checksum
    return checksum & 0xffff


if __name__ == '__main__':
    # Ver http://man7.org/linux/man-pages/man7/raw.7.html
    send_fd = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    # Para receber existem duas abordagens. A primeira é a da etapa anterior
    # do trabalho, de colocar socket.IPPROTO_TCP, socket.IPPROTO_UDP ou
    # socket.IPPROTO_ICMP. Assim ele filtra só datagramas IP que contenham um
    # segmento TCP, UDP ou mensagem ICMP, respectivamente, e permite que esses
    # datagramas sejam recebidos. No entanto, essa abordagem faz com que o
    # próprio sistema operacional realize boa parte do trabalho da camada IP,
    # como remontar datagramas fragmentados. Para que essa questão fique a
    # cargo do nosso programa, é necessário uma outra abordagem: usar um socket
    # de camada de enlace, porém pedir para que as informações de camada de
    # enlace não sejam apresentadas a nós, como abaixo. Esse socket também
    # poderia ser usado para enviar pacotes, mas somente se eles forem quadros,
    # ou seja, se incluírem cabeçalhos da camada de enlace.
    # Ver http://man7.org/linux/man-pages/man7/packet.7.html
    recv_fd = socket.socket(socket.AF_PACKET, socket.SOCK_DGRAM, socket.htons(ETH_P_IP))

    loop = asyncio.get_event_loop()
    loop.add_reader(recv_fd, raw_recv, recv_fd)
    asyncio.get_event_loop().call_later(1, send_ping, send_fd)
    asyncio.get_event_loop().call_soon(check_timeouts)
    loop.run_forever()
