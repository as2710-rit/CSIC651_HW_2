# CSCI-651 Homework 2: Ping and Traceroute

Python 3.8+ implementations of `ping` and `traceroute` using raw sockets.
Standard library only (see `requirements.txt` for doc/lint tools).

## Files
- `my_ping.py` - ping
- `my_traceroute.py` - traceroute
- `utils.py` - shared checksum / ICMP / IP-header helpers

## How to run
Raw sockets need root/administrator rights. On Linux/macOS use `sudo`.
On Windows use an Administrator terminal and allow inbound ICMP in the
firewall. A Linux VM or WSL is the easiest environment.

```bash
pip install -r requirements.txt
```

### Ping
```bash
sudo python3 my_ping.py google.com             # until Ctrl+C
sudo python3 my_ping.py -c 4 google.com        # 4 packets
sudo python3 my_ping.py -c 5 -i 0.5 8.8.8.8    # 0.5 s between packets
sudo python3 my_ping.py -c 3 -s 200 8.8.8.8    # 200 data bytes
sudo python3 my_ping.py -t 5 8.8.8.8           # exit after 5 seconds
```

| Flag | Meaning |
|------|---------|
| `-c count` | stop after sending `count` packets |
| `-i wait` | seconds between packets (default 1) |
| `-s size` | data bytes (default 56) |
| `-t timeout` | exit after this many seconds |

### Traceroute
```bash
sudo python3 my_traceroute.py google.com
sudo python3 my_traceroute.py -n google.com      # numeric addresses only
sudo python3 my_traceroute.py -q 1 google.com    # 1 probe per hop
sudo python3 my_traceroute.py -S -q 5 google.com # unanswered-probe summary
```

| Flag | Meaning |
|------|---------|
| `-n` | do not resolve hop addresses to names |
| `-q nqueries` | probes per TTL (default 3) |
| `-S` | summary of unanswered probes per hop |

## Documentation
```bash
sphinx-quickstart docs     # enable sphinx.ext.autodoc, add ".." to sys.path
cd docs && make latexpdf
```
