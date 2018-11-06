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


def timeout(fd, conexao, seq_no, segment):
    if seq_no in conexao.unacked_segments:
        conexao.seg_in_rtt = conexao.seg_in_rtt/2
        conexao.threshold_found = True
        (dst_addr, dst_port) = conexao.id_conexao[0:2]
        fd.sendto(segment, (dst_addr, dst_port))
        asyncio.get_event_loop().call_later(5, timeout, fd, conexao, seq_no, segment)


def addr2str(addr):
    return '%d.%d.%d.%d' % tuple(int(x) for x in addr)

def str2addr(addr):
    return bytes(int(x) for x in addr.split('.'))

def handle_ipv4_header(packet):
    version = packet[0] >> 4
    ihl = packet[0] & 0xf
    assert version == 4
    src_addr = addr2str(packet[12:16])
    dst_addr = addr2str(packet[16:20])
    segment = packet[4*ihl:]
    return src_addr, dst_addr, segment


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

    
    fd.sendto(segment, (dst_addr, dst_port))
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
        fd.sendto(segment, (dst_addr, dst_port))
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
    src_addr, dst_addr, segment = handle_ipv4_header(packet)
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

        fd.sendto(fix_checksum(make_synack(dst_port, src_port, conexao.seq_no, conexao.ack_no),
                               src_addr, dst_addr),
                  (src_addr, src_port))

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



if __name__ == '__main__':
    fd = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    loop = asyncio.get_event_loop()
    loop.add_reader(fd, raw_recv, fd)
    loop.run_forever()
