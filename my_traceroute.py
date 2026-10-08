#!/usr/bin/env python3
"""A simple implementation of the Linux ``traceroute`` command.

UDP probes are sent with an increasing TTL; routers along the path reply
with ICMP Time Exceeded and the destination replies with ICMP Port
Unreachable.  Requires root/administrator privileges.

Example::

    sudo python3 my_traceroute.py -n -q 2 google.com
"""

import argparse
import select
import socket
import struct
import sys
import time

from utils import (ICMP_DEST_UNREACHABLE, ICMP_TIME_EXCEEDED, parse_ip_header,
                   resolve_host)

MAX_HOPS = 30
BASE_PORT = 33434
PROBE_TIMEOUT = 3.0
PAYLOAD = b"\x00" * 32  # 20 (IP) + 8 (UDP) + 32 = 60 byte packets

# Flags real traceroute prints for ICMP Destination Unreachable codes.
UNREACH_FLAGS = {0: "!N", 1: "!H", 2: "!P", 4: "!F", 5: "!S", 13: "!X"}


def parse_args():
    """Parse command-line arguments.

    :return: Parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Print the route packets take to a network host.")
    parser.add_argument("host", help="destination hostname or IP address")
    parser.add_argument("-n", dest="numeric", action="store_true",
                        help="print hop addresses numerically only")
    parser.add_argument("-q", dest="nqueries", type=int, default=3,
                        help="number of probes per TTL (default 3)")
    parser.add_argument("-S", dest="summary", action="store_true",
                        help="print a summary of unanswered probes per hop")
    args = parser.parse_args()
    if not 1 <= args.nqueries <= 10:
        parser.error("number of queries must be between 1 and 10")
    return args


def probe_port_from_icmp(icmp):
    """Extract the original UDP destination port from an ICMP error.

    The error payload holds the original IP header plus the first 8 bytes
    of the original datagram (the UDP header).

    :param bytes icmp: ICMP message (IP header already removed).
    :return: The destination port of the probe, or ``None``.
    :rtype: int or None
    """
    if len(icmp) < 8 + 20:
        return None
    inner = icmp[8:]
    inner_len = (inner[0] & 0x0F) * 4
    udp = inner[inner_len:inner_len + 8]
    if len(udp) < 8:
        return None
    return struct.unpack("!HH", udp[:4])[1]


def wait_for_icmp(recv_sock, port, deadline):
    """Wait for the ICMP error caused by the probe sent to ``port``.

    :param socket.socket recv_sock: Raw ICMP socket.
    :param int port: UDP destination port of the probe.
    :param float deadline: ``time.perf_counter()`` value to give up at.
    :return: ``(arrival_time, source_ip, icmp_type, icmp_code)`` or None.
    :rtype: tuple or None
    """
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return None
        ready, _, _ = select.select([recv_sock], [], [], remaining)
        if not ready:
            return None
        data, _ = recv_sock.recvfrom(65535)
        arrival = time.perf_counter()
        if len(data) < 20 + 8:
            continue
        header_len, _, src = parse_ip_header(data)
        icmp = data[header_len:]
        icmp_type, icmp_code = icmp[0], icmp[1]
        if icmp_type not in (ICMP_TIME_EXCEEDED, ICMP_DEST_UNREACHABLE):
            continue
        if probe_port_from_icmp(icmp) == port:
            return arrival, src, icmp_type, icmp_code


def describe(addr, numeric, cache):
    """Format a router address for display.

    :param str addr: IPv4 address.
    :param bool numeric: If true, show only the IP address.
    :param dict cache: Reverse-DNS cache.
    :return: ``"name (ip)"`` or just ``"ip"`` with ``-n``.
    :rtype: str
    """
    if numeric:
        return addr
    if addr not in cache:
        try:
            cache[addr] = socket.gethostbyaddr(addr)[0]
        except (socket.herror, socket.gaierror, OSError):
            cache[addr] = addr
    return f"{cache[addr]} ({addr})"


def trace_hop(ttl, dest_ip, args, send_sock, recv_sock, state):
    """Send all probes for one TTL and print the hop line.

    :param int ttl: Current time-to-live value.
    :param str dest_ip: Destination IPv4 address.
    :param argparse.Namespace args: Parsed arguments.
    :param socket.socket send_sock: UDP socket used to send probes.
    :param socket.socket recv_sock: Raw ICMP socket.
    :param dict state: Mutable state holding ``port`` and ``cache``.
    :return: ``(reached_destination, unanswered_probes)``.
    :rtype: tuple
    """
    send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
    print(f"{ttl:2d} ", end="", flush=True)
    last_addr = None
    done = False
    lost = 0
    for _ in range(args.nqueries):
        port = state["port"]
        state["port"] += 1
        start = time.perf_counter()
        send_sock.sendto(PAYLOAD, (dest_ip, port))
        result = wait_for_icmp(recv_sock, port, start + PROBE_TIMEOUT)
        if result is None:
            lost += 1
            print(" *", end="", flush=True)
            continue
        arrival, src, icmp_type, icmp_code = result
        if src != last_addr:
            print(" " + describe(src, args.numeric, state["cache"]),
                  end="")
            last_addr = src
        print(f"  {(arrival - start) * 1000:.3f} ms", end="", flush=True)
        if icmp_type == ICMP_DEST_UNREACHABLE:
            done = True
            if icmp_code in UNREACH_FLAGS:
                print(f" {UNREACH_FLAGS[icmp_code]}", end="")
    print()
    return done, lost


def print_summary(rows, nqueries):
    """Print the ``-S`` summary of unanswered probes per hop.

    :param list rows: ``(ttl, unanswered)`` tuples.
    :param int nqueries: Probes sent per hop.
    """
    print("\nSummary of unanswered probes:")
    print("Hop  Sent  Unanswered")
    for ttl, lost in rows:
        pct = 100 * lost // nqueries
        print(f"{ttl:3d}  {nqueries:4d}  {lost:4d} ({pct}%)")


def main():
    """Run the traceroute program.

    :return: Process exit status.
    :rtype: int
    """
    args = parse_args()
    try:
        dest_ip = resolve_host(args.host)
    except socket.gaierror:
        print(f"{args.host}: Name or service not known", file=sys.stderr)
        return 2
    try:
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                  socket.IPPROTO_ICMP)
    except PermissionError:
        print("traceroute: raw sockets need root/administrator "
              "privileges (try sudo)", file=sys.stderr)
        return 1
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                              socket.IPPROTO_UDP)

    print(f"traceroute to {args.host} ({dest_ip}), {MAX_HOPS} hops max, "
          f"{20 + 8 + len(PAYLOAD)} byte packets")
    state = {"port": BASE_PORT, "cache": {}}
    rows = []
    try:
        for ttl in range(1, MAX_HOPS + 1):
            done, lost = trace_hop(ttl, dest_ip, args, send_sock,
                                   recv_sock, state)
            rows.append((ttl, lost))
            if done:
                break
    except KeyboardInterrupt:
        print()
    finally:
        send_sock.close()
        recv_sock.close()

    if args.summary:
        print_summary(rows, args.nqueries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
