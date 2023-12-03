from subprocess import Popen, PIPE

def find_interface():
#    dev_name = 0 # sets dev_name so that function does not return Null and crash code
    find_device = "ip addr show"
    interface_parse = run_cmd(find_device)
    for line in interface_parse.splitlines():
        if "state UP" in line:
            dev_name = line.split(':')[1]
            return dev_name
    return 1 # avoids returning Null if "state UP" doesn't exist

# find an active IP on the first LIVE network device
def getIP():
    interface = find_interface()
    if interface == 1: # if true, no device is in "state UP", skip IP check
        return "not assigned " # display "IP not assigned"
    ip = "0"
    find_ip = "ip addr show %s" % interface
    ip_parse = run_cmd(find_ip)
    for line in ip_parse.splitlines():
        if "inet " in line:
            ip = line.split(' ')[5]
            ip = ip.split('/')[0]
            return ip # returns IP address, if found
    return "pending      " # display "IP pending" when "state UP", but no IPv4 address yet

# run unix shell command, return as ASCII
def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')