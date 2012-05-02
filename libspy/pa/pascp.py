#!/usr/bin/python

# copyright(c) 2012 Chris La

# A simple scp example for Paramiko.
# Args:
#   1: hostname
#   2: username
#   3: password
#   4: local filename
#   5: remote filename

import getpass
import os
import socket
import sys
import getopt

dirname=os.path.dirname(os.path.realpath(sys.argv[0]))
thisScript=os.path.basename(sys.argv[0])

sys.path.append(dirname + '/..')

import paramiko

# defaults if user does not supply
username = 'automation'
password = 'automation'
localfile =''
targetfile =''
hostname =''
verbose = 0

paramiko.util.log_to_file("/var/tmp/pascp.log")

def usage():
    print "Usage: %s [options]" % (thisScript)
    print "    -f local file name"
    print "    -h host name of machine where file is to be copied to or from"
    print "    -t remote file name"
    print "    -l (optional) user (default = automation)"
    print "    -p (optional) password (default = automation's password)"
    print "    -v (optional) set to 1 if verbose is desired. Default = 0"
    print "Example:"
    print "%s -f myfile -h host -t /tmp/myfile" % (thisScript)

def do_scp(localfile=localfile, hostname=hostname, targetfile=targetfile, username=username, password=password , verbose=verbose):
    # Socket connection to remote host
    if (verbose == '1'):
        print "scp %s %s:%s@%s:%s" %(localfile, username, password, hostname, targetfile)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, 22))

    # Build a SSH transport
    t = paramiko.Transport(sock)
    #t.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
    t.start_client()
    t.auth_password(username, password)

    # Start a scp channel
    scp_channel = t.open_session()
          
    f = file(localfile, 'rb')
    scp_channel.exec_command('scp -v -t %s\n'
                             % '/'.join(targetfile.split('/')[:-1]))
    scp_channel.send('C%s %d %s\n'
                 %(oct(os.stat(localfile).st_mode)[-4:],
                   os.stat(localfile)[6],
                   targetfile.split('/')[-1]))
    scp_channel.sendall(f.read())

    # Cleanup
    f.close()
    scp_channel.close()
    t.close()
    sock.close()

#Main
ERROR=-1
argc = len(sys.argv)
if (argc < 2):
    usage()
    sys.exit(ERROR)

try:
    opts, args = getopt.getopt(sys.argv[1:], "l:p:f:t:h:v:", ["username=", "password=", "localfile=", "hostname=", "targetfile=", "verbose="])
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(ERROR)

for o, a in opts:
    if o in ("-l", "--username") :
        username = a
    elif o in ("-p", "--password") :
        password = a
    elif o in ("-h", "--hostname") :
        hostname = a
    elif o in ("-f", "--localfile") :
        localfile = a
    elif o in ("-t", "--targetfile") :
        targetfile = a
    elif o in ("-v", "--verbose") :
        verbose = a
    else:
        assert False, "unhandled option"
        sys.exit(ERROR)

do_scp(localfile, hostname, targetfile, username, password, verbose )
