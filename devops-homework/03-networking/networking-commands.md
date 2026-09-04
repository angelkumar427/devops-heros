# Networking Fundamentals — Commands, Output, and What I Understood

Every command below was actually executed, and the raw transcripts are in [`commands-output-1.txt`](./commands-output-1.txt) and [`commands-output-2.txt`](./commands-output-2.txt).

**Where these ran:** a `debian:stable-slim` container on a Linux Docker host (`Linux 6.8.0-117-generic aarch64`), with `iproute2`, `iputils-ping`, `dnsutils`, `curl`, `traceroute` and `netcat-openbsd` installed.

**One caveat, stated up front:** that Docker host is a VM whose outbound traffic goes through a **user-mode network stack**, which answers ICMP itself instead of forwarding it. So `ping` round-trip times are artificially low (sub-millisecond to `8.8.8.8`) and `traceroute` sees only the first hop before everything times out. DNS, TCP-connect and HTTP results are genuine; the ICMP *timings and hop paths* are not representative of a real internet path. Each affected command says so below.

---

## `ip a` — list network interfaces & addresses

```
$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
2: eth0@if126: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether f2:b6:a8:4e:56:f9 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0

$ ip -br addr        # brief form
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0@if126       UP             172.17.0.2/16
```

**What I understood:** `ip a` (short for `ip address show`) is the modern replacement for `ifconfig`. It lists every network interface and the addresses bound to it. Here I see `lo` (loopback, `127.0.0.1`) and `eth0` with `172.17.0.2/16` — that `/16` in the `172.17.x.x` range is Docker's **default bridge** subnet, so the address itself tells me this process is inside a container on `docker0`. The `@if126` suffix is the veth pair's peer interface index on the host side: the container end of a virtual cable whose other end is plugged into the bridge. `ip -br addr` gives the same thing in one line per interface, which is much easier to scan.

```
$ ip route
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

The default gateway `172.17.0.1` is the `docker0` bridge on the host — every packet leaving this container goes through it.

## `ping` — reachability & round-trip latency

```
$ ping -c 4 8.8.8.8
64 bytes from 8.8.8.8: icmp_seq=1 ttl=63 time=0.111 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=63 time=0.506 ms
--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3063ms
rtt min/avg/max/mdev = 0.111/0.412/0.521/0.174 ms
```

**What I understood:** `ping` sends ICMP echo-request packets and waits for echo-replies, reporting round-trip time and packet loss — the classic first check for "is there any path to this host at all." `-c 4` stops after four packets instead of running forever. The three numbers that matter are **packet loss** (0% here = no drops), **rtt avg** (typical latency) and **mdev** (jitter — how much the latency varies, which matters a lot for calls and gaming).

**Caveat for this run:** 0.4 ms to `8.8.8.8` is not a real internet RTT. The VM's user-mode network stack replies to the ICMP probe itself rather than sending it to Google, so what I measured is the round trip to the local stack. From a normal host I'd expect roughly 10–50 ms. The command and its output format are exactly the same; only the numbers are an artifact of the environment.

## `dig` — detailed DNS lookup

```
$ dig +short github.com
20.207.73.82

$ dig github.com
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 57779
;; QUESTION SECTION:
;github.com.                    IN      A
;; ANSWER SECTION:
github.com.             0       IN      A       20.207.73.82
;; Query time: 0 msec
;; SERVER: 192.168.5.1#53(192.168.5.1) (UDP)
```

**What I understood:** `dig` queries DNS directly and shows the whole transaction: the **status** (`NOERROR` = the name exists and resolved; `NXDOMAIN` would mean it doesn't), the **question** asked, the **answer** with its record type (`A` = IPv4 address) and **TTL**, and crucially **which resolver answered** (`SERVER: 192.168.5.1#53` — the VM's built-in DNS, port 53). `dig +short` strips it to just the IP, which is what you want in a script. When something "can't be reached", `dig` is how you separate "DNS is broken" from "the host is down" — a `NOERROR` with an answer proves DNS is fine and the problem is further along.

## `nslookup` — simpler/legacy DNS lookup

```
$ nslookup github.com
Server:         192.168.5.1
Address:        192.168.5.1#53

Non-authoritative answer:
Name:   github.com
Address: 20.207.73.82
```

**What I understood:** Same job as `dig` — resolve a hostname via DNS — but older, with terser output and less detail. "Non-authoritative answer" means this came from a caching resolver rather than from GitHub's own authoritative nameservers, which is normal for everyday lookups. `dig` is the better tool when actually debugging (it shows TTLs, flags and query time); `nslookup` is fine for a quick "what's the IP".

## `curl -I` — fetch just the HTTP response headers

```
$ curl -I https://api.github.com
HTTP/2 200
date: Fri, 04 Sep 2026 13:55:23 GMT
cache-control: public, max-age=60, s-maxage=60
```

**What I understood:** `-I` sends a `HEAD` request, so the server returns headers and no body — the fastest way to check whether a service is alive, what it returns, and whether caching or a redirect is in play, without downloading the payload. `HTTP/2 200` confirms both a successful response *and* that the connection negotiated HTTP/2 over TLS. Where `ping` tests the network and `dig` tests DNS, this tests the **application layer** — the thing users actually care about.

## `ss` — show open/listening sockets (modern `netstat`)

```
$ ss -tulpn
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp   LISTEN 0      1            0.0.0.0:8000      0.0.0.0:*    users:(("nc",pid=3518,fd=3))
```

**What I understood:** `ss -tulpn` lists listening sockets — `-t` TCP, `-u` UDP, `-l` listening only, `-p` show the owning process, `-n` numeric ports instead of service names. This answers "what is actually listening on this box, and which process owns it": here a `nc` process (started deliberately for this demo) holding `0.0.0.0:8000`. `0.0.0.0` means "all interfaces" — reachable from outside — whereas `127.0.0.1:8000` would mean loopback-only and unreachable from another machine. That distinction is the usual explanation for "it works locally but not from outside." It's also how you find whatever is squatting on a port you need.

## `traceroute` — show the hop-by-hop path to a host

```
$ traceroute -m 5 8.8.8.8
traceroute to 8.8.8.8 (8.8.8.8), 5 hops max, 60 byte packets
 1  172.17.0.1 (172.17.0.1)  0.094 ms  0.009 ms  0.008 ms
 2  * * *
 3  * * *
```

**What I understood:** `traceroute` maps the routers a packet crosses by sending probes with an increasing TTL; each router that discards a packet for "TTL exceeded" reveals itself in the process. `-m 5` caps it at five hops. It's the tool for localising *where* a path breaks or slows: three fast hops then a jump to 300 ms points at the specific link responsible. `* * *` means a hop didn't reply — routers are often configured not to, so gaps are normal and don't by themselves mean a fault.

**Caveat for this run:** hop 1 is `172.17.0.1`, the `docker0` bridge, and everything after that is `* * *` — the VM's user-mode network stack doesn't forward the probes at all. On a normal host I'd see the local router, then the ISP, then progressively distant hops.

## `nc` (netcat) — test whether a specific TCP port is open

```
$ nc -zv -w3 8.8.8.8 443
Connection to 8.8.8.8 443 port [tcp/*] succeeded!

$ nc -zv -w3 github.com 443
Connection to github.com (20.207.73.82) 443 port [tcp/*] succeeded!

$ nc -zv -w3 8.8.8.8 23        # a port that is NOT open
nc: connect to 8.8.8.8 port 23 (tcp) timed out: Operation now in progress
(exit 1)
```

**What I understood:** `-z` is zero-I/O mode (test the connection, send nothing), `-v` verbose, `-w3` a 3-second timeout so it can't hang. This is the most targeted reachability test available: `ping` only tells you ICMP got through, while `nc -zv` proves a **specific TCP port** accepts connections — which is the actual question when a service won't connect. The contrast between the two results above is the useful part: port 443 succeeds, port 23 (telnet, correctly closed everywhere) times out. A timeout usually means a firewall silently dropping packets, whereas "connection refused" means the host answered but nothing is listening — two different problems with two different fixes.

## Summary — when to reach for which tool

| Question | Command |
|---|---|
| Is the network stack up / what's my IP / where does traffic exit? | `ip a`, `ip route` |
| Is there *any* path to this host? (ICMP) | `ping` |
| What IP does this hostname resolve to, and which resolver said so? | `dig` / `nslookup` |
| Is this specific service actually reachable? | `curl -I` (HTTP) or `nc -zv` (any TCP port) |
| What's listening locally, and which process owns it? | `ss -tulpn` |
| Where along the path is it breaking? | `traceroute` |

The single most useful lesson from running these together: **each one tests a different layer**, so the fastest way to diagnose "it doesn't work" is to walk up the stack — `ip a` (is my interface configured) → `ping` (is there a route) → `dig` (does the name resolve) → `nc -zv` (is the port open) → `curl -I` (does the application answer). Whichever step fails first tells you which team owns the problem.
