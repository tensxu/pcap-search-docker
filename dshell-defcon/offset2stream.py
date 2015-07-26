#!/usr/bin/env python2

import sys
import struct
import socket

ff = open(sys.argv[1], 'rb')
offset = int(sys.argv[2])

ff.seek(-4, 2)
total_conns = struct.unpack('I', ff.read(4))[0]
ff.seek(-4 * (1 + total_conns), 2)
len_conns = list(struct.unpack('I' * total_conns, ff.read(4 * total_conns)))

_out_file = sys.stdout

def out_end_str(*args):
    if _out_file != sys.stdout:
        _out_file.close()
out_end_repr = out_end_hex = out_end_str

def out_begin_hex(*args):
    global _out_file
    _out_file = open(sys.argv[5], 'wb')
out_begin_str = out_begin_repr = out_begin_hex


def out_pcap(*args):
    pass
out_end_pcap = out_pcap


def out_repr(srcip, srcport, destip, dstport, data):
    print >>_out_file, socket.inet_ntoa(struct.pack('I', srcip)) + ':' + str(srcport),
    print >>_out_file, ' --> ',
    print >>_out_file, socket.inet_ntoa(struct.pack('I', destip)) + ':' + str(dstport),
    print >>_out_file, '(%d bytes)' % len(data)
    print >>_out_file, repr(data)

def out_hex(srcip, srcport, destip, dstport, data):
    print >>_out_file, socket.inet_ntoa(struct.pack('I', srcip)) + ':' + str(srcport),
    print >>_out_file, ' --> ',
    print >>_out_file, socket.inet_ntoa(struct.pack('I', destip)) + ':' + str(dstport),
    print >>_out_file, '(%d bytes)' % len(data)
    print >>_out_file, data.encode('hex')


def out_str(srcip, srcport, destip, dstport, data):
    print >>_out_file, socket.inet_ntoa(struct.pack('I', srcip)) + ':' + str(srcport),
    print >>_out_file, ' --> ',
    print >>_out_file, socket.inet_ntoa(struct.pack('I', destip)) + ':' + str(dstport),
    print >>_out_file, '(%d bytes)' % len(data)
    print >>_out_file, str(data)

def out_begin_pcap(_pkts):
    import dpkt
    import pcap
    pkts = list(_pkts)
    reader = pcap.pcap(sys.argv[4])
    writer = dpkt.pcap.Writer(open(sys.argv[5], 'wb'))
    cnt = 0
    while True:
        try:
            i = reader.next()
            cnt += 1
            if cnt in pkts:
                writer.writepkt(str(i[1]), i[0])
                pkts.remove(cnt)
            if len(pkts) == 0:
                break
        except StopIteration:
            break
    assert(pkts == [])
    writer.close()




out = eval('out_' + sys.argv[3])
out_begin = eval('out_begin_' + sys.argv[3])
out_end = eval('out_end_' + sys.argv[3])

current_offset = 0
found = False
for i in len_conns:
    if current_offset <= offset < current_offset + i:
        found = True
        ff.seek(current_offset, 0)
        len_pkt, cliip, servip, cliport, servport = struct.unpack('IIIHH', ff.read(16))
        cnt_pkt = struct.unpack('I', ff.read(4))[0]
        pkts_id = struct.unpack('I' * cnt_pkt, ff.read(4 * cnt_pkt))
        out_begin(pkts_id)
        for i in xrange(len_pkt):
            direction = ff.read(1)
            len_data = struct.unpack('I', ff.read(4))[0]
            data = ff.read(len_data)
            if direction == 'c':
                out(cliip, cliport, servip, servport, data)
            else:
                out(servip, servport, cliip, cliport, data)
        out_end()
        break
    current_offset += i

ff.close()

if not found:
    sys.exit(5)
