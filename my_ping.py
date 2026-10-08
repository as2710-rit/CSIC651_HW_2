#!/usr/bin/env python3
"""A simple implementation of the Linux ``ping`` command.

Sends ICMP Echo Requests over a raw socket and prints the replies in the
same format as the real ping.  Requires root/administrator privileges.

Example::

    sudo python3 my_ping.py -c 4 google.com
"""

import argparse
import math
import os
import select
import socket
import struct
import sys
import time

from utils import (ICMP_ECHO_REPLY, build_echo_request, parse_ip_header,
                   resolve_host)

ICMP_HEADER_LEN = 8
IP_HEADER_LEN = 20


def parse_args():
    """Parse command-line arguments.

    :return: Parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Send ICMP ECHO_REQUEST packets to a host.")
    parser.add_argument("host", help="destination hostname or IP address")
    parser.add_argument("-c", dest="count", type=int, default=None,
                        help="stop after sending COUNT packets")
    parser.add_argument("-i", dest="wait", type=float, default=1.0,
                        help="seconds to wait between packets (default 1)")
    parser.add_argument("-s", dest="size", type=int, default=56,
                        help="number of data bytes to send (default 56)")
    parser.add_argument("-t", dest="timeout", type=float, default=None,
                        help="exit after this many seconds")
    args = parser.parse_args()
    if args.count is not None and args.count < 1:
        parser.error("bad number of packets to transmit")
    if args.wait <= 0:
        parser.error("bad wait time")
    if not 0 <= args.size <= 65507 - ICMP_HEADER_LEN:
        parser.error("illegal packet size")
    return args


def make_payload(size):
    """Create a payload of ``size`` bytes with an incrementing pattern.

    :param int size: Number of data bytes.
    :return: Payload bytes.
    :rtype: bytes
    """
    return bytes((i + 8) % 256 for i in range(size))


def wait_for_reply(sock, ident, seq, deadline):
    """Wait for the Echo Reply that matches ``ident`` and ``seq``.

    :param socket.socket sock: Raw ICMP socket.
    :param int ident: Expected ICMP identifier.
    :param int seq: Expected sequence number.
    :param float deadline: ``time.perf_counter()`` value to give up at.
    :return: ``(arrival_time, source_ip, ttl, icmp_length)`` or ``None``.
    :rtype: tuple or None
    """
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return None
        ready, _, _ = select.select([sock], [], [], remaining)
        if not ready:
            return None
        data, _ = sock.recvfrom(65535)
        arrival = time.perf_counter()
        if len(data) < IP_HEADER_LEN + ICMP_HEADER_LEN:
            continue
        header_len, ttl, src = parse_ip_header(data)
        icmp = data[header_len:]
        if len(icmp) < ICMP_HEADER_LEN:
            continue
        r_type, _, _, r_id, r_seq = struct.unpack("!BBHHH", icmp[:8])
        if r_type == ICMP_ECHO_REPLY and r_id == ident and r_seq == seq:
            return arrival, src, ttl, len(icmp)


def print_stats(host, sent, rtts, elapsed_ms):
    """Print the summary shown when ping finishes.

    :param str host: Destination as typed by the user.
    :param int sent: Packets transmitted.
    :param list rtts: Round-trip times in milliseconds.
    :param float elapsed_ms: Total running time in milliseconds.
    """
    received = len(rtts)
    loss = 100.0 * (sent - received) / sent if sent else 0.0
    print(f"\n--- {host} ping statistics ---")
    print(f"{sent} packets transmitted, {received} received, "
          f"{loss:.0f}% packet loss, time {elapsed_ms:.0f}ms")
    if rtts:
        avg = sum(rtts) / received
        mdev = math.sqrt(max(sum(r * r for r in rtts) / received
                             - avg * avg, 0.0))
        print(f"rtt min/avg/max/mdev = {min(rtts):.3f}/{avg:.3f}/"
              f"{max(rtts):.3f}/{mdev:.3f} ms")


def main():
    """Run the ping program.

    :return: Process exit status (0 if any reply was received).
    :rtype: int
    """
    args = parse_args()
    try:
        dest_ip = resolve_host(args.host)
    except socket.gaierror:
        print(f"ping: {args.host}: Name or service not known",
              file=sys.stderr)
        return 2
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                             socket.IPPROTO_ICMP)
    except PermissionError:
        print("ping: raw sockets need root/administrator privileges "
              "(try sudo)", file=sys.stderr)
        return 1

    ident = os.getpid() & 0xFFFF
    payload = make_payload(args.size)
    total = args.size + ICMP_HEADER_LEN + IP_HEADER_LEN
    print(f"PING {args.host} ({dest_ip}) {args.size}({total}) "
          f"bytes of data.")

    start = time.perf_counter()
    stop_at = start + args.timeout if args.timeout is not None else None
    rtts = []
    sent = 0
    seq = 0
    try:
        while args.count is None or sent < args.count:
            if stop_at is not None and time.perf_counter() >= stop_at:
                break
            seq += 1
            packet = build_echo_request(ident, seq & 0xFFFF, payload)
            send_time = time.perf_counter()
            sock.sendto(packet, (dest_ip, 0))
            sent += 1

            interval_end = send_time + args.wait
            deadline = max(interval_end, send_time + 1.0)
            if stop_at is not None:
                deadline = min(deadline, stop_at)
            result = wait_for_reply(sock, ident, seq & 0xFFFF, deadline)
            if result:
                arrival, src, ttl, length = result
                rtt = (arrival - send_time) * 1000
                rtts.append(rtt)
                print(f"{length} bytes from {src}: icmp_seq={seq} "
                      f"ttl={ttl} time={rtt:.1f} ms")
            # Sleep out the rest of the interval before the next packet.
            if args.count is None or sent < args.count:
                pause = interval_end - time.perf_counter()
                if stop_at is not None:
                    pause = min(pause, stop_at - time.perf_counter())
                if pause > 0:
                    time.sleep(pause)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

    elapsed_ms = (time.perf_counter() - start) * 1000
    print_stats(args.host, sent, rtts, elapsed_ms)
    return 0 if rtts else 1


if __name__ == "__main__":
    sys.exit(main())
