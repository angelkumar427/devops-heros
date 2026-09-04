# Linux Command Reference (Quick Guide)

A working reference of the commands used most often as a DevOps/SysAdmin, grouped by purpose.

## File & directory navigation

```bash
pwd                     # print working directory
ls -la                  # list all files, long format, incl. hidden
cd /path/to/dir         # change directory
tree -L 2               # directory tree, 2 levels deep
find . -name "*.log"    # find files by name pattern
find . -mtime -1         # files modified in the last 1 day
locate filename          # fast search using a prebuilt index (mlocate)
```

## File operations

```bash
cp -r src/ dst/          # copy, recursive
mv old new                # move / rename
rm -rf dir/               # remove recursively, force (careful!)
touch file.txt             # create empty file / update timestamp
mkdir -p a/b/c              # create nested dirs
cat file.txt                # print file contents
less file.txt                # paginated view
head -n 20 file.txt            # first 20 lines
tail -n 20 -f file.txt           # last 20 lines, follow (live tail)
grep -rn "pattern" .              # recursive, line-numbered search
sed -i 's/foo/bar/g' file.txt      # in-place find & replace
awk '{print $1}' file.txt           # column extraction
diff file1 file2                     # compare two files
wc -l file.txt                        # line count
```

## Permissions & ownership

```bash
chmod 755 script.sh        # rwxr-xr-x
chmod +x script.sh          # add execute bit
chown user:group file       # change owner + group
umask                        # default permission mask
```

## Links

```bash
ln original.txt hard.txt      # hard link
ln -s original.txt soft.txt    # symbolic link
```
(full write-up: [`01-soft-vs-hard-links.md`](./01-soft-vs-hard-links.md))

## Users & groups

```bash
adduser username           # interactive user creation (Debian/Ubuntu)
useradd -m -s /bin/bash u    # explicit, scriptable user creation
usermod -aG sudo username     # add user to a group
passwd username                 # set/change password
deluser / userdel username       # remove a user
groups username                   # list a user's groups
id username                        # uid/gid/groups info
su - username                       # switch user
sudo <command>                       # run as root
```
(full write-up: [`02-adduser-vs-useradd.md`](./02-adduser-vs-useradd.md))

## Processes

```bash
ps aux                     # all running processes
ps aux --sort=-%mem | head   # top memory consumers
top / htop                    # live process viewer
kill -9 <pid>                  # force kill
killall processname             # kill by name
pgrep -f pattern                 # find PIDs matching pattern
nohup cmd &                       # run detached from terminal
jobs / fg / bg                     # job control
nice -n 10 cmd / renice 10 -p pid    # scheduling priority
```

## Disk & filesystem

```bash
df -h                      # disk free, human-readable
du -sh *                    # size of each item in current dir
mount / umount /dev/sdb1 /mnt   # mount/unmount
lsblk                        # list block devices
fdisk -l                      # partition table info
```

## System info & logging

```bash
uname -a                   # kernel/OS info
uptime                      # load average + uptime
free -h                      # memory usage
hostname / hostnamectl        # machine name
journalctl -u service -f       # service logs (see 03-journalctl.md)
dmesg | tail                    # kernel ring buffer
```

## Networking
(full write-up with live output: [`../03-networking/networking-commands.md`](../03-networking/networking-commands.md))

```bash
ip a                       # interfaces & IPs (modern)
ifconfig                    # interfaces & IPs (legacy)
ping -c 4 host                # reachability test
curl -I https://example.com    # HTTP headers only
ss -tulpn                       # listening sockets (modern netstat)
dig example.com / nslookup       # DNS lookups
traceroute host                   # path to a host
```

## Archives & compression

```bash
tar -czvf out.tar.gz dir/    # create gzip tarball
tar -xzvf out.tar.gz          # extract
zip -r out.zip dir/            # zip
unzip out.zip                   # unzip
```

## Package management (Debian/Ubuntu)

```bash
apt update && apt upgrade   # refresh index / upgrade packages
apt install <pkg>            # install
apt remove <pkg>              # remove
dpkg -l | grep <pkg>           # check if installed
```

## Environment & shell

```bash
echo $VAR                  # print a variable
export VAR=value            # set env var for this shell + children
env                          # list all env vars
which cmd / type cmd          # locate a binary / resolve alias
history                        # command history
alias ll='ls -la'               # define a shortcut
crontab -e / crontab -l          # edit / list scheduled jobs
```

## Redirection & pipes

```bash
cmd > file        # stdout to file (overwrite)
cmd >> file         # stdout to file (append)
cmd 2> file           # stderr to file
cmd > file 2>&1        # both stdout and stderr to file
cmd1 | cmd2              # pipe stdout of cmd1 into cmd2
```
