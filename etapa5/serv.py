#!/usr/bin/python3
#
# Antes de usar, execute o seguinte comando para evitar que o Linux feche
# as conexões TCP abertas por este programa:
#
# sudo iptables -I OUTPUT -p tcp --tcp-flags RST RST -j DROP
#

import asyncio
import socket
import struct
import os
import random
import time

Pacotes = {}

ETH_P_ALL = 0x0003
ETH_P_IP  = 0x0800


ICMP = 0x01  # https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers


# Coloque abaixo o endereço IP do seu computador na sua rede local
src_ip = '192.168.15.31'

# Coloque aqui o nome da sua placa de rede
if_name = 'wlp2s0'

# Coloque aqui o endereço MAC do roteador da sua rede local (arp -a | grep _gateway)
dest_mac = 'ac:c6:62:b4:59:45'

# Coloque aqui o endereço MAC da sua placa de rede (ip link show dev wlan0)
src_mac = '5c:c9:d3:8f:88:95'

FLAGS_FIN = 1<<0
FLAGS_SYN = 1<<1
FLAGS_RST = 1<<2
FLAGS_ACK = 1<<4

MSS = 1460
WINDOW_SIZE = 100
RTT = .001 # sim, deveria ser calculado, mas tratado aqui como constante

INITIAL_SEQ = 0

class Conexao:
    def __init__(self, id_conexao, seq_no, ack_no):
        self.id_conexao = id_conexao
        self.seq_no = seq_no
        global INITIAL_SEQ
        INITIAL_SEQ = seq_no
        self.ack_no = ack_no
        self.send_queue = b"HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\n\r\n" + 1000000 * b"hello pombo\n"
        self.unacked_segments = []
        self.window_size = 0
        self.handshake_done = False
        self.closing_connection = False
        self.seg_in_rtt = 1 # for slow start
        self.seg_in_rtt_counter = 1
        self.threshold_found =  False
conexoes = {}


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


# Timeout TCP
def timeout(fd, conexao, seq_no, segment):
    if seq_no in conexao.unacked_segments:
        conexao.seg_in_rtt = conexao.seg_in_rtt/2
        conexao.threshold_found = True
        (dst_addr, dst_port) = conexao.id_conexao[0:2]
        send_ip(fd, segment, ICMP, dst_addr)
        asyncio.get_event_loop().call_later(5, timeout, fd, conexao, seq_no, segment)


def addr2str(addr):
    return '%d.%d.%d.%d' % tuple(int(x) for x in addr)

def str2addr(addr):
    return bytes(int(x) for x in addr.split('.'))

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


def make_synack(src_port, dst_port, seq_no, ack_no):
    return struct.pack('!HHIIHHHH', src_port, dst_port, seq_no,
                       ack_no, (5<<12)|FLAGS_ACK|FLAGS_SYN,
                       1024, 0, 0)


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

def fix_checksum(segment, src_addr, dst_addr):
    pseudohdr = str2addr(src_addr) + str2addr(dst_addr) + \
        struct.pack('!HH', 0x0006, len(segment))
    seg = bytearray(segment)
    seg[16:18] = b'\x00\x00'
    seg[16:18] = struct.pack('!H', calc_checksum(pseudohdr + seg))
    return bytes(seg)

def send_eth(fd, datagram, protocol):
    eth_header = mac_addr_to_bytes(dest_mac) + \
        mac_addr_to_bytes(src_mac) + \
        struct.pack('!H', protocol)
    fd.send(eth_header + datagram)

ip_pkt_id = 0
def send_ip(fd, msg, protocol, dest_ip):
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


def send_next(fd, conexao):
    conexao.seg_in_rtt_counter -= 1
    initial_point = (conexao.seq_no - INITIAL_SEQ) - 1
    final_point = initial_point + MSS
    payload = conexao.send_queue[initial_point:final_point]

    (dst_addr, dst_port, src_addr, src_port) = conexao.id_conexao

    segment = struct.pack('!HHIIHHHH', src_port, dst_port, conexao.seq_no,
                          conexao.ack_no, (5<<12)|FLAGS_ACK,
                          1024, 0, 0) + payload

   

    segment = fix_checksum(segment, src_addr, dst_addr)

    
    send_ip(fd, segment, ICMP, dst_addr)
    asyncio.get_event_loop().call_later(5, timeout, fd, conexao, conexao.seq_no, segment)
    conexao.seq_no = (conexao.seq_no + len(payload)) & 0xffffffff
    conexao.unacked_segments.append(conexao.seq_no)
    

    if conexao.send_queue[final_point:] == b"":
        segment = struct.pack('!HHIIHHHH', src_port, dst_port, conexao.seq_no,
                          conexao.ack_no, (5<<12)|FLAGS_FIN|FLAGS_ACK,
                          0, 0, 0)
        segment = fix_checksum(segment, src_addr, dst_addr)
        conexao.closing_connection = True
        conexao.unacked_segments.append(conexao.seq_no+1)
        send_ip(fd, segment, ICMP, dst_addr)
    elif conexao.window_size<=WINDOW_SIZE:
        if conexao.seg_in_rtt_counter <= 0:
            if not conexao.threshold_found:
                conexao.seg_in_rtt *= 2 # grows exponentially
            else:
                conexao.seg_in_rtt += 1 # grows linearly
            conexao.seg_in_rtt_counter = conexao.seg_in_rtt
            asyncio.get_event_loop().call_later(RTT, send_next, fd, conexao)
        else:
            asyncio.get_event_loop().call_later(0.0000000001, send_next, fd, conexao)


def raw_recv(fd):
    packet = fd.recv(12000)

    dst_mac_frame = frame[0:6]
    protocol_frame = frame[12:14]

    # Verificar se endereco MAC
    # recebido eh o da sua placa
    # e o protocolo
    if(dst_mac_frame == mac_addr_to_bytes(src_mac) and  protocol_frame == struct.pack('!H', ETH_P_IP)):
        print('recebido quadro de %d bytes' % len(frame))

        packet = frame[14:]
        identification, flags, fragment_offset, src_addr, segment = handle_ipv4_header(packet)

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
                print('\tConteúdo: ',segment, '\n')
    
                src_port, dst_port, seq_no, ack_no, \
                    flags, window_size, checksum, urg_ptr = \
                    struct.unpack('!HHIIHHHH', segment[:20])

                id_conexao = (src_addr, src_port, dst_addr, dst_port)

                if dst_port != 7000:
                    return

                payload = segment[4*(flags>>12):]

                if (flags & FLAGS_SYN) == FLAGS_SYN:
                    print('%s:%d -> %s:%d (seq=%d)' % (src_addr, src_port,
                                                    dst_addr, dst_port, seq_no))

                    conexoes[id_conexao] = conexao = Conexao(id_conexao=id_conexao,
                                                            seq_no=struct.unpack('I', os.urandom(4))[0],
                                                            ack_no=seq_no + 1)

                    send_ip(fd, fix_checksum(make_synack(dst_port, src_port, conexao.seq_no, conexao.ack_no), src_addr, dst_addr), ICMP, src_addr)
                    conexao.seq_no += 1
                    conexao.window_size = 1
                    conexao.unacked_segments.append(conexao.seq_no)
                elif id_conexao in conexoes:
                    conexao = conexoes[id_conexao]
                    if ack_no >= conexao.unacked_segments[0]:
                        if not conexao.handshake_done:
                            conexao.handshake_done = True
                            return
                        if conexao.closing_connection and len(conexao.unacked_segments)==1:
                            del conexoes[id_conexao]
                            return
                        for unacked_object in conexao.unacked_segments:
                            if unacked_object<=ack_no:
                                conexao.window_size -= 1
                                conexao.unacked_segments.remove(unacked_object)
                                conexao.ack_no += len(payload)                    
                        asyncio.get_event_loop().call_later(.1, send_next, fd, conexao)
                else:
                    print('%s:%d -> %s:%d (pacote associado a conexão desconhecida)' %
                        (src_addr, src_port, dst_addr, dst_port))

def ip_addr_to_bytes(addr):
    return bytes(map(int, addr.split('.')))


def mac_addr_to_bytes(addr):
    return bytes(int('0x'+s, 16) for s in addr.split(':'))


if __name__ == '__main__':
    fd = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    fd.bind((if_name, 0))

    loop = asyncio.get_event_loop()
    loop.add_reader(fd, raw_recv, fd)
    asyncio.get_event_loop().call_soon(check_timeouts)
    loop.run_forever()
