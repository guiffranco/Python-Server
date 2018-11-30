import socket
import asyncio
import struct
import time


Pacotes = {}

ETH_P_ALL = 0x0003
ETH_P_IP  = 0x0800


ICMP = 0x01  # https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers


# Coloque aqui o endereço de destino para onde você quer mandar o ping
dest_ip = '192.168.15.1'

# Coloque abaixo o endereço IP do seu computador na sua rede local
src_ip = '192.168.15.31'

# Coloque aqui o nome da sua placa de rede
if_name = 'wlp2s0'

# Coloque aqui o endereço MAC do roteador da sua rede local (arp -a | grep _gateway)
dest_mac = 'ac:c6:62:b4:59:45'

# Coloque aqui o endereço MAC da sua placa de rede (ip link show dev wlan0)
src_mac = '5c:c9:d3:8f:88:95'

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

def send_eth(fd, datagram, protocol):
    eth_header = mac_addr_to_bytes(dest_mac) + \
        mac_addr_to_bytes(src_mac) + \
        struct.pack('!H', protocol)
    fd.send(eth_header + datagram)


ip_pkt_id = 0
def send_ip(fd, msg, protocol):
    global ip_pkt_id
    ip_header = bytearray(struct.pack('!BBHHHBBH',
                            0x45, 0,
                            20 + len(msg),
                            ip_pkt_id,
                            0,
                            15,
                            protocol,
                            0) +
                          ip_addr_to_bytes(src_ip) +
                          ip_addr_to_bytes(dest_ip))
    ip_header[10:12] = struct.pack('!H', calc_checksum(ip_header))
    ip_pkt_id += 1
    send_eth(fd, ip_header + msg, ETH_P_IP)


def send_ping(fd):
    print('enviando ping')
    # Exemplo de pacote ping (ICMP echo request) com payload grande
    msg = bytearray(b"\x08\x00\x00\x00" + 2*b"\xba\xdc\x0f\xfe")
    msg[2:4] = struct.pack('!H', calc_checksum(msg))

    send_ip(fd, msg, ICMP)

    asyncio.get_event_loop().call_later(1, send_ping, fd)


def raw_recv(recv_fd):
    frame = fd.recv(12000)

    dst_mac_frame = frame[0:6]
    protocol_frame = frame[12:14]
    
    # Verificar se endereco MAC
    # recebido eh o da sua placa
    # e o protocolo
    if(dst_mac_frame == mac_addr_to_bytes(src_mac) and  protocol_frame == struct.pack('!H', ETH_P_IP)):
        print('recebido quadro de %d bytes' % len(frame))

        packet = frame[14:]
        identification, flags, fragment_offset, src_addr, segment = handle_ipv4_header(packet)
        
        
        if(src_addr != dest_ip):
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

        # evita fragmentos repetidos
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

def ip_addr_to_bytes(addr):
    return bytes(map(int, addr.split('.')))


def mac_addr_to_bytes(addr):
    return bytes(int('0x'+s, 16) for s in addr.split(':'))


if __name__ == '__main__':
    # Ver http://man7.org/linux/man-pages/man7/raw.7.html
    fd = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    fd.bind((if_name, 0))

    loop = asyncio.get_event_loop()
    loop.add_reader(fd, raw_recv, fd)
    asyncio.get_event_loop().call_later(1, send_ping, fd)
    asyncio.get_event_loop().call_soon(check_timeouts)
    loop.run_forever()
