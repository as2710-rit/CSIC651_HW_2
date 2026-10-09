<div align="center">

# 🌐 My Ping & Traceroute

**Pure-Python re-implementations of `ping` and `traceroute` built on raw sockets**

![Python](https://img.shields.io/badge/python-3.6%2B-3776AB?logo=python&logoColor=white)
![Protocol](https://img.shields.io/badge/protocol-ICMP%20%7C%20UDP-6f42c1)
![Dependencies](https://img.shields.io/badge/dependencies-none-2ea44f)
![Privileges](https://img.shields.io/badge/requires-root%20%2F%20sudo-d73a49)

</div>

---

##  Project Structure

| File | Purpose |
|:-----|:--------|
|  `my_ping.py` | Sends ICMP Echo Requests and prints replies and statistics (macOS-style output) |
|  `my_traceroute.py` | Sends UDP probes with increasing TTL and prints each hop (macOS-style output) |
|  `utils.py` | Shared helpers: Internet checksum, ICMP packet builder, IP header parser, host resolver |

> Keep all three files in the **same directory**: both programs import from `utils.py`.

---

##  Requirements

- **Python 3.6+** (uses f-strings; standard library only, nothing to `pip install`)
- **Root / administrator privileges**, because both programs open raw ICMP sockets
- Works on macOS and Linux

---

## How to Run

```bash
# 1. Go to the project folder
cd path/to/project

# 2. Run with sudo (raw sockets need elevated privileges)
sudo python3 my_ping.py <options> <host>
sudo python3 my_traceroute.py <options> <host>
```

>  Without `sudo` you will see:
> `raw sockets need root/administrator privileges (try sudo)`

---

## How to Interrupt the continuous stream

> Press Ctrl+C in the terminal while continuous stream to raise a Keyboard Interrupt and to stop the Ping or Traceroute program.


---

## `my_ping.py`

**Syntax:** `sudo python3 my_ping.py [-c COUNT] [-i WAIT] [-s SIZE] [-t TIMEOUT] host`

### Options

| Flag | Argument | Default | Description |
|:----:|:--------:|:-------:|:------------|
| `-c` | `COUNT` | ∞ | Stop after sending `COUNT` packets |
| `-i` | `WAIT` | `1.0` | Seconds to wait between packets |
| `-s (only lower case s)` | `SIZE` | `56` | Number of data bytes to send (0 to 65499) |
| `-t` | `TIMEOUT` | none | Exit after this many seconds |
| | `host` | required | Destination hostname or IP address |

### Example Commands

| # | Command | What it does |
|:-:|:--------|:-------------|
| 1 | `sudo python3 my_ping.py google.com` | Ping continuously until you press `Ctrl+C` |
| 2 | `sudo python3 my_ping.py -c 4 google.com` | Send exactly 4 packets, then print statistics |
| 3 | `sudo python3 my_ping.py -c 5 -i 0.5 8.8.8.8` | Send 5 packets, one every half second |
| 4 | `sudo python3 my_ping.py -c 3 -s 128 google.com` | Send 3 packets carrying 128 data bytes each |
| 5 | `sudo python3 my_ping.py -t 10 google.com` | Run for 10 seconds, then stop |
| 6 | `sudo python3 my_ping.py -c 2 127.0.0.1` | Ping the local machine (loopback test) |

### Sample Output

```text
$ sudo python3 my_ping.py -c 4 google.com
PING google.com (142.250.190.46): 56 data bytes
64 bytes from 142.250.190.46: icmp_seq=0 ttl=117 time=12.481 ms
64 bytes from 142.250.190.46: icmp_seq=1 ttl=117 time=11.907 ms
64 bytes from 142.250.190.46: icmp_seq=2 ttl=117 time=13.226 ms
64 bytes from 142.250.190.46: icmp_seq=3 ttl=117 time=12.054 ms

--- google.com ping statistics ---
4 packets transmitted, 4 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 11.907/12.417/13.226/0.520 ms
```

---

## `my_traceroute.py`

**Syntax:** `sudo python3 my_traceroute.py [-n] [-q NQUERIES] [-S] host`

### Options

| Flag | Argument | Default | Description |
|:----:|:--------:|:-------:|:------------|
| `-n` | none | off | Print hop addresses numerically (skips reverse DNS lookups) |
| `-q` | `NQUERIES` | `3` | Number of probes per TTL (1 to 10) |
| `-S (only upper case s)` | none | off | Print a summary of unanswered probes per hop |
| | `host` | required | Destination hostname or IP address |

### Example Commands

| # | Command | What it does |
|:-:|:--------|:-------------|
| 1 | `sudo python3 my_traceroute.py google.com` | Standard trace with hostnames and 3 probes per hop |
| 2 | `sudo python3 my_traceroute.py -n google.com` | Numeric output only, which is faster (no DNS lookups) |
| 3 | `sudo python3 my_traceroute.py -q 1 google.com` | One probe per hop for a quick trace |
| 4 | `sudo python3 my_traceroute.py -n -q 2 8.8.8.8` | Numeric output with 2 probes per hop |
| 5 | `sudo python3 my_traceroute.py -S google.com` | Show the unanswered-probes summary table at the end |
| 6 | `sudo python3 my_traceroute.py -n -q 2 -S google.com` | Combine all options |

### Sample Output

```text
$ sudo python3 my_traceroute.py -n -q 2 google.com
traceroute to google.com (142.250.190.46), 64 hops max, 40 byte packets
 1  192.168.1.1  1.842 ms  1.310 ms
 2  10.20.0.1  8.455 ms  7.981 ms
 3  * *
 4  72.14.215.85  11.204 ms  10.876 ms
 5  142.250.190.46  12.097 ms  11.733 ms
```

### Sample Output with `-S`

```text
traceroute to google.com (142.250.65.78), 64 hops max, 40 byte packets
 1  gnat2-vrrp-vlan4018.rit.edu (10.118.255.253)  13.048 ms *  9.153 ms
 2  * 129.21.255.124 (129.21.255.124)  106.312 ms *
 3  rit-east-pp-rtr001-100g-vlan856.net.rit.edu (129.21.8.126)  11.895 ms  7.956 ms  7.351 ms
 4  buf-9208-rit-cdn.nysernet.net (199.109.111.9)  8.459 ms  98.711 ms  9.456 ms
 5  buf-55a1-buf-9208-cdn.nysernet.net (199.109.107.213)  8.881 ms  8.198 ms  10.274 ms
 6  199.109.107.145 (199.109.107.145)  9.366 ms  11.237 ms  13.020 ms
 7  bin-540-rit-540-cdn.nysernet.net (199.109.107.142)  17.331 ms  16.470 ms  14.855 ms
 8  nyc111-57c3-bin-540-cdn.nysernet.net (199.109.107.118)  16.211 ms  16.293 ms  19.368 ms
 9  lclgaa-ax-in-f14.1e100.net (142.250.65.78)  16.781 ms  17.123 ms  17.196 ms
Summary of unanswered probes:
Hop  Sent  Unanswered
  1     3     1 (33%)
  2     3     2 (66%)
  3     3     0 (0%)
  4     3     0 (0%)
  5     3     0 (0%)
  6     3     0 (0%)
  7     3     0 (0%)
  8     3     0 (0%)
  9     3     0 (0%)
```


---

##  How It Works

| Tool | Technique |
|:-----|:----------|
| **ping** | Builds an ICMP Echo Request (type 8) with a valid checksum, sends it over a raw socket, then matches the Echo Reply (type 0) by identifier and sequence number to compute the round-trip time |
| **traceroute** | Sends UDP datagrams to ports starting at 33434 with TTL = 1, 2, 3, and so on. Each router that drops a packet returns ICMP *Time Exceeded* (type 11), and the destination returns ICMP *Port Unreachable* (type 3), which ends the trace |

---

## Troubleshooting

| Problem | Fix |
|:--------|:----|
| `raw sockets need root/administrator privileges` | Re-run the command with `sudo` |
| `ModuleNotFoundError: No module named 'utils'` | Run from the folder that contains `utils.py` |
| `Name or service not known` | Check the spelling of the hostname or your DNS and internet connection |
| Rows of `* * *` in traceroute | Some routers and firewalls silently drop probes, which is normal |

---

<div align="center">

Made with Python and raw sockets

</div>