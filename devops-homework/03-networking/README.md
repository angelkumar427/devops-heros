# Task 3 — Networking Fundamentals

## What the assignment asked

1. **Practice the commands and repo shared in the devops-hero GitHub repository.** That's this repository — the course material is in [`../../session4-networking/`](../../session4-networking/): [`ip.md`](../../session4-networking/ip.md) (IP classes, subnet masks, host-count maths) and [`resources.md`](../../session4-networking/resources.md) (practice repos on network troubleshooting, OSI/network devices, subnetting, DHCP, NetFlow/NTP).
2. **Create a Markdown file, execute the networking commands, add the output, and explain what you understood about each one.** → [`networking-commands.md`](./networking-commands.md), with the raw transcripts in [`commands-output-1.txt`](./commands-output-1.txt) and [`commands-output-2.txt`](./commands-output-2.txt).

**Where these ran:** a `debian:stable-slim` container on a Linux Docker host (`Linux 6.8.0-117-generic aarch64`) with `iproute2`, `iputils-ping`, `dnsutils`, `curl`, `traceroute` and `netcat-openbsd` installed. Every command below was really executed.

---

## The eight commands, with real output

### `ip a` — interfaces and addresses

```
$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0@if126       UP             172.17.0.2/16

$ ip route
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

**Understood:** the modern replacement for `ifconfig`. The `172.17.0.0/16` address tells me this is Docker's default bridge, so the machine is a container; `@if126` is the veth pair's peer index on the host — the other end of a virtual cable plugged into `docker0`, which is also the default gateway.

### `ping` — reachability and latency

```
$ ping -c 4 8.8.8.8
64 bytes from 8.8.8.8: icmp_seq=1 ttl=63 time=0.111 ms
4 packets transmitted, 4 received, 0% packet loss, time 3063ms
rtt min/avg/max/mdev = 0.111/0.412/0.521/0.174 ms
```

**Understood:** sends ICMP echo-requests and reports round-trip time and loss — the first "is there any path at all" check. The three numbers that matter are **packet loss**, **rtt avg** and **mdev** (jitter, which is what breaks calls and games). *Caveat: 0.4 ms to `8.8.8.8` is not a real internet RTT — see the note at the bottom.*

### `dig` — detailed DNS lookup

```
$ dig +short github.com
20.207.73.82

$ dig github.com
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 57779
;; ANSWER SECTION:
github.com.             0       IN      A       20.207.73.82
;; SERVER: 192.168.5.1#53(192.168.5.1) (UDP)
```

**Understood:** shows the whole DNS transaction — `status: NOERROR` (the name exists; `NXDOMAIN` would mean it doesn't), the record type (`A` = IPv4), the TTL, and crucially **which resolver answered**. This is how you separate "DNS is broken" from "the host is down": a `NOERROR` with an answer proves DNS is fine and the fault is further along.

### `nslookup` — simpler DNS lookup

```
$ nslookup github.com
Server:         192.168.5.1
Address:        192.168.5.1#53

Non-authoritative answer:
Name:   github.com
Address: 20.207.73.82
```

**Understood:** same job, older and terser. "Non-authoritative" means a caching resolver answered rather than GitHub's own nameservers, which is normal. `dig` is the better debugging tool (TTLs, flags, query time); `nslookup` is fine for a quick IP.

### `curl -I` — HTTP response headers only

```
$ curl -I https://api.github.com
HTTP/2 200
date: Fri, 04 Sep 2026 13:55:23 GMT
cache-control: public, max-age=60, s-maxage=60
```

**Understood:** `-I` sends a `HEAD` request, so you get headers and no body — the fastest check that a service is alive, and what caching or redirects are in play. `HTTP/2 200` confirms both success and that HTTP/2 was negotiated. Where `ping` tests the network and `dig` tests DNS, this tests the **application layer**.

### `ss` — listening sockets

```
$ ss -tulpn
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp   LISTEN 0      1            0.0.0.0:8000      0.0.0.0:*    users:(("nc",pid=3518,fd=3))
```

**Understood:** `-t` TCP, `-u` UDP, `-l` listening only, `-p` owning process, `-n` numeric ports. Answers "what is listening, and who owns it". The `0.0.0.0` vs `127.0.0.1` distinction is the important one: `0.0.0.0` means all interfaces and reachable from outside, `127.0.0.1` means loopback-only — which is the usual explanation for "it works locally but not from another machine".

### `traceroute` — the hop-by-hop path

```
$ traceroute -m 5 8.8.8.8
traceroute to 8.8.8.8 (8.8.8.8), 5 hops max, 60 byte packets
 1  172.17.0.1 (172.17.0.1)  0.094 ms  0.009 ms  0.008 ms
 2  * * *
```

**Understood:** sends probes with increasing TTL; each router that discards one for "TTL exceeded" reveals itself. It localises *where* a path slows or breaks — three fast hops then a jump to 300 ms names the guilty link. `* * *` means a hop chose not to reply, which is common and not itself a fault.

### `nc` — is a specific TCP port open?

```
$ nc -zv -w3 8.8.8.8 443
Connection to 8.8.8.8 443 port [tcp/*] succeeded!

$ nc -zv -w3 8.8.8.8 23          # a port that is NOT open
nc: connect to 8.8.8.8 port 23 (tcp) timed out: Operation now in progress
(exit 1)
```

**Understood:** `-z` tests the connection without sending data, `-w3` caps the wait. The most targeted reachability test there is: `ping` only proves ICMP got through, while this proves a **specific port** accepts connections. The contrast above is the useful part — and *how* it fails matters: a **timeout** means a firewall silently dropping packets, whereas **"connection refused"** means the host replied but nothing is listening. Two different problems, two different fixes.

---

## Summary — which tool for which question

| Question | Command |
|---|---|
| Is the stack up / what's my IP / where does traffic exit? | `ip a`, `ip route` |
| Is there *any* path to this host? | `ping` |
| What does this name resolve to, and who said so? | `dig` / `nslookup` |
| Is this specific service reachable? | `curl -I` (HTTP) or `nc -zv` (any TCP port) |
| What's listening locally, and who owns it? | `ss -tulpn` |
| Where along the path is it breaking? | `traceroute` |

**The main thing I took away:** each command tests a *different layer*, so the fastest way to diagnose "it doesn't work" is to walk up the stack — `ip a` → `ping` → `dig` → `nc -zv` → `curl -I`. Whichever step fails first tells you which layer, and often which team, owns the problem.

## One honest caveat about this environment

The Docker host here is a VM whose outbound traffic goes through a **user-mode network stack**, which answers ICMP itself instead of forwarding it. So `ping` round-trip times are artificially low and `traceroute` sees only the first hop before timing out. **DNS, TCP-connect and HTTP results are genuine**; the ICMP *timings and hop paths* are not representative of a real internet path. Flagged here and per-command rather than presented as real numbers.
