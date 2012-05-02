#!/usr/bin/env python

"""
copyright(c) 2012 Chris La

This module runs ssh command on remote machines
It implements the Passh class for use by other python scripts.
It can also be run directly as a cli (python passh.py)

"""

Inline = False 

import sys
import os
import getopt

dirname = os.path.dirname(os.path.realpath(sys.argv[0]))
_thisScript = os.path.basename(sys.argv[0]).split('.')[0].strip()

# add local directories to lib path so that it can run from any location
sys.path.append(dirname + '/.')
sys.path.append(dirname + '/..')

#print "%s" %(sys.path)
#exit()

import paramiko

#__all__ = ["run_ssh","Passh"]

# defaults
username = 'automation'
password = 'automation'
host = '' 
cmd = ''
verbose = '0'

LOG_FILENAME = '/var/tmp/passh.log'

class NoCMDexception (Exception):
    """ For command line errors """
    pass

class Passh(object):

  def __init__(self, host=host, username=username, password=password, verbose=verbose, doReturn=None):
    self.host = host
    self.username = username
    self.password = password
    self.verbose = verbose
    self.doReturn = doReturn

  def run_ssh(self, cmd=None, host=None, username=None, password=None, verbose=None, doReturn=None, simulate=None):

    if cmd is None:
        raise NoCMDexception('Did not specify a command to run on remote host.')

    # if user does not pass in options, try getting it from self object
    if host is None:
        host = self.host

    if username is None:
        username = self.username

    if password is None:
        password = self.password

    if verbose is None:
        verbose = self.verbose

    if doReturn is None:
        doReturn = self.doReturn

    if verbose == '1':
        print "executing ssh host=%s username=%s password=%s cmd='%s'" %(self.host, username, password, cmd)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 

    # log to file
    paramiko.util.log_to_file(LOG_FILENAME)

    try:
        #print "creating connection"
        ssh.connect(host, username=username, password=password)

        #print "connected"

        stdinData= []
        stdoutData = []
        stderrData = []

        # run the command
        if simulate is True:
            print "\n*** Simulation mode. Not actually running this command. ***\n"
            print "   %s" %cmd
            #print "\n *** Simulation mode end ***\n" 
        else:
            stdin, stdout, stderr = ssh.exec_command(cmd) 
            #for line in stdin:
            #    stdinData.append(line)
            for line in stdout:
                stdoutData.append(line)
            for line in stderr:
                stderrData.append(line)

            #print stdout.read()
            #for line in stdout:
            #    print line.strip('\n')
            #for line in stderr:
            #    print line.strip('\n')

    finally:
       #print "closing connection"
       ssh.close()
       #print "closed"

    # print or return retults
    if doReturn is True:
        #print "%s: return instead of print result" %_thisFile   #XXX debug
        return stdoutData, stderrData
    else:
        for line in stdoutData:
            print line.strip("\n")
        for line in stderrData:
            print line.strip("\n")


if __name__ == "__main__" and not Inline:

    ERROR=-1

    def usage():
        print "Usage: %s [options]" % (_thisScript)
        print "    -h host"
        print "    -c command"
        print "    -l optional user (default = automation)"
        print "    -p optional password (defauilt = automation's password)"
        print "    -v (optional) set to 1 for verbose (default = 0)"
        print "Example:"
        print "%s -h yardgnome -c 'uname -a'" % (_thisScript)

    argc = len(sys.argv)
    if (argc < 2):
        print "\nThis program runs commands on a remote host via ssh.\n"
        usage()
        sys.exit(ERROR)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "l:p:c:h:v:", ["user=", "password=", "host=", "command=", "verbose=", "example"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(ERROR)

    for o, a in opts:
        if o in ("-l", "--user") :
            username = a
        elif o in ("-p", "--password") :
            password = a
        elif o in ("-h", "--host") :
            host = a
        elif o in ("-c", "--command") :
            cmd = a
        elif o in ("-v", "--verbose") :
            verbose = a
        elif o in ("--example") :
            host = "yardgnome"
            cmd = "uname -a" 
            verbose = '1'
        else:
            assert False, "unhandled option"
            sys.exit(ERROR)

    try:
        ps=Passh(host=host, username=username, password=password, verbose=verbose)
        ps.run_ssh(cmd=cmd)
    except Exception, e:
        print "Error: %s" %e
