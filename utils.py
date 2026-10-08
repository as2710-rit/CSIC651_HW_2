"""Shared helpers for my_ping.py and my_traceroute.py.

This module contains the Internet checksum, ICMP packet construction and
IP header parsing used by both programs.
"""

import socket
import struct

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_DEST_UNREACHABLE = 3
ICMP_TIME_EXCEEDED = 11


def checksum(data):
    """Compute the 16-bit Internet checksum (RFC 1071).

    :param bytes data: Data to checksum.
    :return: The one's complement checksum.
    :rtype: int
    """
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def build_echo_request(ident, seq, payload):
    """Build an ICMP Echo Request packet.

    :param int ident: ICMP identifier (usually derived from the PID).
    :param int seq: Sequence number.
    :param bytes payload: Data bytes appended after the ICMP header.
    :return: The complete ICMP packet with a valid checksum.
    :rtype: bytes
    """
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, ident, seq)
    csum = checksum(header + payload)
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, csum, ident, seq)
    return header + payload


def parse_ip_header(data):
    """Parse the fixed fields of an IPv4 header.

    :param bytes data: Raw packet beginning with an IPv4 header.
    :return: Tuple ``(header_length, ttl, source_ip)``.
    :rtype: tuple
    """
    header_len = (data[0] & 0x0F) * 4
    ttl = data[8]
    src = socket.inet_ntoa(data[12:16])
    return header_len, ttl, src


def resolve_host(host):
    """Resolve a hostname or dotted address to an IPv4 address.

    :param str host: Hostname or IP address.
    :return: IPv4 address as a string.
    :rtype: str
    :raises socket.gaierror: If the name cannot be resolved.
    """
    return socket.gethostbyname(host)
