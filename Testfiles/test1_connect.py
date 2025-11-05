import socket

print("="*60)
print("  CONNECTIVITY TEST")
print("="*60)

# Test port scanning
print("\n[1] Testing port scan capability...")
ip = "127.0.0.1"
ports = [80, 443, 445, 135, 139]
found = []

for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        if sock.connect_ex((ip, port)) == 0:
            found.append(port)
        sock.close()
    except:
        pass

if found:
    print("    [OK] Can scan ports. Found:", found)
else:
    print("    [INFO] No ports open on localhost")

# Test network info
print("\n[2] Network Information...")
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print("    Hostname:", hostname)
    print("    Local IP:", local_ip)
except Exception as e:
    print("    [ERROR]", e)

print("\n" + "="*60)
