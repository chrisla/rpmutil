#!/usr/bin/env python

"""
copyright(c) 2012 Chris La

This module runs rpm command on remote machines, using ssh via paramiko
It implements several class for use by other python scripts.
It can also be run directly as a cli (python passh.py)

"""

Inline = False 

import sys
import os
import getopt
import re
import string
import time
#import logger

#logging.handlers.SMTPHandler(mailhost, fromaddr, toaddrs, subject[, credentials])

dirname = os.path.dirname(os.path.realpath(sys.argv[0]))

#strip out any .py part
_thisScript = os.path.basename(sys.argv[0]).split('.')[0].strip()

# add local directories to lib path so that it can run from any location
sys.path.append(dirname + '/.')
sys.path.append(dirname + '/..')
#sys.path.append(dirname + '/scripts/passh/')

#insert at beginning of path
#sys.path.insert(0,dirname + '/scripts/passh/')

#print "%s" %(sys.path)
#exit()

if not Inline:
    from pa.passh import Passh 
#    import passh
#    Passh = passh.passh.Passh

#import  passh.passh
#print dir(Passh)
#import passh

# Linux source defaults
buildHost = 'build1' 
buildName = 'automation'
buildPass = 'automation'

# Linux_Host defaults
vmHost = None
vmUser = 'root'
vmPass = 'vmPassword'

class ParseUtils(object):
    def parse_ini(self, inList=None, delimiter='='):

        """
        Parse ini files with format:
        KEY = VALUE

        will properly handles lines with comments, such as:
        KEY = VALUE    #this is a comment
        """

        COMMENT_CHAR = '#'
        OPTION_CHAR = delimiter 

        options = {}
        for line in inList:
            # First, remove comments:
            if COMMENT_CHAR in line:
                # split on comment char, keep only the part before
                line, comment = line.split(COMMENT_CHAR, 1)

            # Second, find lines with an option=value:
            if OPTION_CHAR in line:
                # split on option char:
                option, value = line.split(OPTION_CHAR, 1)
                #print option, "|", value  #XXX

                # strip spaces:
                option = option.strip()
                value = value.strip()

                # store in dictionary:
                options[option] = value

        #print options #XXX
        return options
            

class OSUtil(object):
    """
    Determine what OS type and version
    """
    def get_uname_a(self, verbose=False):
        """
        Run uname -a and return the result
        """
    
        if verbose: print "Determining Linux Machine OS type and version ..."

        UnameA = ""

        try:
            cmd = "uname -a"
            if verbose: print "\n  %s" %cmd
            vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel, doReturn=True)
            stdoutData, stderrData = vm.run_ssh(cmd=cmd)
            if verbose:
                for line in stdoutData:
                    print "  (reply)", line.strip('\n')

                for line in stderrData:
                    print "  (error)", line.strip('\n')

            if len(stdoutData) == 1 and not stderrData:
                UnameA = stdoutData[0].strip()

        except Exception, e:
            print "Error: %s" %e

        return UnameA

    def get_os_release(self, verbose=False):
        """
        run cat /etc/redhat-release or /etc/SuSE-release, and return the result 
        Such as "Red Hat Linux release 5.4 (final)" or

                SUSE Linux Enterprise Server 11 (x86_64)
                VERSION = 11
                PATCHLEVEL = 0
        """
        if verbose: print "reading /etc/*release ..."

        vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel, doReturn=True)

        OSTypeList = dict(redhat='/etc/redhat-release', \
                            sles='/etc/SuSE-release')
        #OSTypeList = {'redhat': '/etc/redhat-release', 'sles': '/etc/SuSE-release'}
        OsType = None
        OSFile = None

        # check where is the /etc/redhat-release, or its equivilant file
        for key, value in OSTypeList.items():
            #print "key is", key, ". value is", value

            if verbose: print "\n  check if '%s' exists on Linux Machine " % value

            cmd = "[[ -f %s ]] && echo yes || echo no" % value
            stdoutData, stderrData = vm.run_ssh(cmd=cmd)

            if verbose:
                for line in stdoutData:
                    print "  (reply)", line.strip('\n')

                for line in stderrData:
                    print "  (error)", line.strip('\n')

            if "yes\n" in stdoutData:
                if verbose: print "\n==> This os is '%s' family" %key 
                OSType = key
                OSFile = value
                break

        cmd = "cat %s" %OSFile
        if verbose: print "\n  %s" % cmd
        stdoutData, stderrData = vm.run_ssh(cmd=cmd)

        return stdoutData, stderrData 

    def get_os_info_str(self):

        """
        return a string like sles10sp3 or centos54u164.
        This string is used to narrow down the list of Linux drivers to the correct one to use for update.
        This is done by looking at the /etc/*release file, and the output of uname -a.
        """ 
        """
        /etc/SuSE-release
        SUSE Linux Enterprise Server 10 (x86_64)
        VERSION = 10
        PATCHLEVEL = 3
        """
        """
        /etc/redhat-release
        CentOS release 4.2 (Final)
        """

        # XXX TODO: pass these in, instead of using global

        
        vmos = OSUtil()
        stdoutData, stderrData = vmos.get_os_release(verbose=verbose)

        if verbose:
            for line in stdoutData:
                print "  (reply)", line.strip('\n')

            for line in stderrData:
                print "  (error)", line.strip('\n')

        #print stdoutData  #XXX debug
        if verbose: print "\n  parsing version information"

        # if "release" is in the first line, we have a centos/rhel
        if re.search('.+release \d+', stdoutData[0]):
            if verbose: print "  confirmed is RHEL/CENTOS"
            OSType = "centos"
            # match the digit(s) and dot(s) after the word "release". for example 'release 5.4'
            m = re.search(r'.+release ([0-9\.]+ )', stdoutData[0])
            # OSVer is the digit part, with period removed.
            OSVer = m.group(1).strip().replace(".","")   
            if verbose: print "  OSVer =", OSVer

            OSData = OSType + OSVer

        # if SUSE is in the first line, it is sles
        elif re.match('SUSE', stdoutData[0]):
            if verbose: print "  confirmed is SUSE"
            # OSVer = take the 2nd line, split it at the "=" and take the 2nd half, stripped.
            OSType = "sles"
            OSVer = stdoutData[1].split('=')[1].strip()
            OSSubVer = stdoutData[2].split('=')[1].strip()

            # only use "spD" format if D is not zero
            if OSSubVer == '0': OSSubVer = ""
            else: OSSubVer = "sp"+OSSubVer

            if verbose: print "OSVer", OSVer, ", OSSubVer", OSSubVer

            OSData = OSType + OSVer + OSSubVer
        else:
            # if we cant figure it out, return unknown os 
            OSData = "UnknownOS"

        if verbose: print "  OSData =", OSData

        return OSData

    def get_os_update_version(self, verbose=None):

        """
        Get the OS update version. For example, from 'uname -r' we get 2.6.18-164.el5
        The update version is the '164' part.
        We will split by '-' and take the second half (164.el5), then we split again by '.'
        and take the first part (164).

        """

        # get the output of uname -r
        # XXX TODO: pass these in, instead of using global
        vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel, doReturn=True)
        cmd = "uname -r"
        if verbose: print "\n  %s" %cmd
        stdoutData, stderrData = vm.run_ssh(cmd=cmd)
        if verbose: print "  (reply) %s" %stdoutData[0]

        words = stdoutData[0].strip("\n").split("-",1)
        if verbose: print "Split ", stdoutData[0].strip(), " by '-' into", words

        # in some cases, uname returns a string with more than one "-", for example 2.6.27.19-5-default
        # we will treat the second or more "-" as a "."
        updatePart = words[1].replace("-",".").split(".")
        if verbose: print "Split ", words[1], " by '.' into", updatePart 

        # remove the last element from the list, which is usually the "el5" or "smp" part of the update string
        if len(updatePart) > 1 : updatePart.pop()   
        if verbose: print "Update part, with last element removed", updatePart 

        update = "".join(updatePart).strip()
        if verbose: print "the update string is", update

        return update
        
class RPMUtil(object):
    """
    Utilities to update, query, erase Linux drivers in a virtual machine OS 
    """

    def  __init__(self, simulate=None):
        self.simulate = simulate

    def show_fe(self, buildType="official", buildNum=None):
        """
        show what drivers are available for updating
        """
        try:
            if buildNum == 'latest':
                bld = Passh(host=buildHost, username=buildName, password=buildPass, verbose=VerboseLevel, doReturn=True)
                matchString = "???"
                cmd = "cd /import/automation/builds/server1 && /bin/ls -1drt %s-%s 2>/dev/null" \
                     %(buildType, matchString)
                stdoutData, stderrData = bld.run_ssh(cmd=cmd)
                buildNum = stdoutData[-1].strip().split('-')[1]
                print "The latest build is '%s'" %buildNum

            if buildNum == None:
                regEx = "*"
                print "Available driver builds:"
                bld = Passh(host=buildHost, username=buildName, password=buildPass, verbose=VerboseLevel, doReturn=True)
                cmd = "cd /import/automation/builds/server1 && /bin/ls -1drt %s-%s" \
                    %(buildType, regEx)
                stdoutData, stderrData = bld.run_ssh(cmd=cmd)
                if stderrData and "No such file or directory" in stderrData[0].strip():
                    print "Warning: Did not find any builds."
                else:
                    for line in stdoutData: 
                        # we only want to show the symlinks such as "official-123", not the long form
                        if not re.search(r'\.', line):
                            print line.strip()
                    for line in stderrData: print line.strip()
            else:
                # a build num is passed in
                bld = Passh(host=buildHost, username=buildName, password=buildPass, verbose=VerboseLevel, doReturn=True)
                cmd = "cd /import/automation/builds/server1/%s-%s/packages && /bin/ls -1rtL *fedriver*" %(buildType, buildNum)
                stdoutData, stderrData = bld.run_ssh(cmd=cmd)
                if stderrData and "No such file or directory" in stderrData[0].strip():
                    print "Error: No such build '%s'" %buildNum
                else:
                    print "Builds %s Linux driver files:" %buildNum
                    for line in stdoutData: print line.strip()
                    for line in stderrData: print line.strip()

        except Exception, e:
            print "Error: %s" %e

    def query_fe(self):
        """
        query Linux_Host for the Linux driver installed, if any
        """
        try:
            vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel)
            cmd = "rpm -qa|grep fedrivers"
            vm.run_ssh(cmd=cmd)
        except Exception, e:
            print "Error: %s" %e

    def update_fe(self, buildType="official", buildNum=None, simulate=None):
        """
        update the fe driver on Linux_Host.
        """
        #print "executing updateFE"

        # if user does not pass in options, try getting it from self object
        if simulate is None:
            simulate = self.simulate

        if buildNum is None:
            print "Error: Unable to update driver because 'build' not specified"
            sys.exit(-1) # XXX todo: raise exception instead

        if buildNum == 'latest':
            bld = Passh(host=buildHost, username=buildName, password=buildPass, verbose=VerboseLevel, doReturn=True)
            matchString = "???"
            cmd = "cd /import/automation/builds/server1 && /bin/ls -1drt %s-%s 2>/dev/null" \
                 %(buildType, matchString)
            stdoutData, stderrData = bld.run_ssh(cmd=cmd)
            buildNum = stdoutData[-1].strip().split('-')[1]
            print "\nThe latest build is '%s'" %buildNum

        if simulate:
            print " \n*** simulation mode. Not actually running the commands ***\n"

        try:

            # determine what version we need
            vmos=OSUtil()
            stdoutData, stderrData = vmos.get_os_release(verbose=verbose)

            # if we get bad data, just substitute a string for OSRelease
            if stdoutData and not stderrData:
                OSRelease = stdoutData[0].strip()
            else:
                OSRelease = "Unknown OS"

            print "Determine the Linux driver for Linux_Host %s '%s'" %(vmHost, OSRelease)
            OSData = vmos.get_os_info_str()
            OSString = OSData

            # get the correct build from build machine

            bld = Passh(host=buildHost, username=buildName, password=buildPass, verbose=VerboseLevel, doReturn=True)

            # if update string is 0, we pretend it doesnt exist. otherwise we put "u" in front of the update string.
            OSUpdate = vmos.get_os_update_version(verbose=verbose)
            if OSUpdate == '0': OSUpdate = ""
            else: OSUpdate ="u" + OSUpdate
            OSString = OSData + OSUpdate

            cmd = "cd /import/automation/builds/server1/%s-%s/packages && /bin/ls -1rtL *fedriver*%s-*|grep -v installer" \
                %(buildType, buildNum, OSString)
            stdoutData, stderrData = bld.run_ssh(cmd=cmd)

            if verbose:
                #print "stdoutData"
                for line in stdoutData:
                    print line.strip('\n')

                #print "stderr"
                for line in stderrData:
                    print line.strip('\n')

            # if we got only one return and no error, then we found our driver and it is an exact match
            if len(stdoutData) == 1 and not stderrData and "fedrivers" in stdoutData[0]:
                Driver = stdoutData[0].strip()
                print "\n  FOUND exact match. Driver rpm is: \n\n   %s" % Driver 
             
            # if we got an error, try again without the OS version string
            elif (stderrData and "No such file" in stderrData[0]):

                if verbose: print "WARNING: exact match not not found. Trying without update string."
                OSString = OSData
                cmd = "cd /import/automation/builds/server1/%s-%s/packages && /bin/ls -1rtL *fedriver*%s-*|grep -v installer" \
                    %(buildType, buildNum, OSString)
                stdoutData, stderrData = bld.run_ssh(cmd=cmd)

                if len(stdoutData) == 1 and not stderrData and "fedrivers" in stdoutData[0]:
                    #  found an close match
                    Driver = stdoutData[0].strip()
                    print "\n  FOUND a close match. Driver rpm is: \n\n   %s" % Driver 
                else:
                    print "ERROR: Did NOT find a driver for this build and Linux_Host OS."
                    sys.exit(ERROR) #XXX

            # if we got more than one matches, we need to ask the user to specify which they want 
            elif (len(stdoutData) > 1 and not stderrData and "fedrivers" in stdoutData[0]):
                print "Warning: more than one matching drivers found:"
                for line in stdoutData: print line.strip('\n')
                print "Please indicate which driver to use by specifying (to be determined) options"
                sys.exit(ERROR) #XXX TODO: add a cli option to specify which of the drivers to use

            # build numbers such as "official-123" are symlinked to a real directory.
            # So we get the real dir instead of symlink, which we need for http get later
            cmd = "ls -l /import/automation/builds/server1/%s-%s" %(buildType, buildNum)
            stdoutData, stderrData = bld.run_ssh(cmd=cmd)
            if not stderrData and len(stdoutData) == 1:
                RealDir = stdoutData[0].split("->")[1]
                RealDir = os.path.basename(RealDir).strip()
                if verbose: print "%s-%s is symlinked to %s" %(buildType, buildNum, RealDir)
            else:
                print "Error: Unable to determine the actual directory for %s-%s. Aborting." (buildType, buildNum)
                sys.exit(ERROR)

            # update the build on the Linux_Host, or simulate that if the user requested
            # in simulation, we just run uname on the Linux_Host, and if that succeeds, we assume other command should succeed.
            vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel, doReturn=True)
            if simulate is True:
                if verbose: print "\n *** simulation mode. Not actually running the commands ***\n"
                print "\nContacting Linux_Host..."
                cmd = "uname"
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                if verbose: print stdoutData[0] #XXX

                if len(stdoutData) == 1 and not stderrData and stdoutData[0].strip() == "Linux":
                    print "\nSuccessfully logged into Linux_Host %s as %s/%s" %(vmHost, vmUser, vmPass)
                    print "\nWould try to download http://myserver1/builds/server1/%s/packages/%s" %(RealDir, Driver)
                    print "\nWould try to run 'cd /tmp && rpm -Uvh %s %s'" %(rpmOptions, Driver)
                else:
                    print "ERROR: Would FAIL to log in to the Linux_Host %s as %s/%s" %(vmHost, vmUser, vmPass)
                    print "ERROR: Would abort here."

                print "\n *** simulation completed ***"
            else:
                print "\n +++ UPDATING THE Linux_Host with this driver in 10 seconds. +++"
                print "\n +++ Press control-C now if you want to abort. +++\n"
                time.sleep(10)

                cmd = "cd /tmp && curl -O http://myserver1/builds/server1/%s/packages/%s" %(RealDir, Driver)
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                if verbose: 
                    print "\nExecuting: %s\n" %cmd
                    for line in stdoutData: print line.strip('\n')
                    for line in stderrData: print line.strip('\n')

                ErrorFound = False
                print "------------------------------------------------------------------------"
                cmd = "cd /tmp && rpm -Uvh %s %s" %(rpmOptions, Driver)
                print "rpm -Uvh %s %s" %(rpmOptions, Driver)
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                for line in stdoutData: 
                    if re.search('WARNING|FATAL|nvalid', line): ErrorFound = True
                    print line.strip('\n')
                for line in stderrData: 
                    if re.search('WARNING|FATAL|nvalid', line): ErrorFound = True
                    print line.strip('\n')
                print "------------------------------------------------------------------------"
                if ErrorFound:
                    print "\nWARNING: Errors or Warnings encountered while updating driver. Please check." 

                print "\nThe following driver is installed on the Linux_Host:\n"
                cmd = "rpm -qa|grep fedrivers"
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                for line in stdoutData: print "\t",line.strip('\n')
                for line in stderrData: print "\t",line.strip('\n')
                print "\nDone"
        except Exception, e:
            print "Error: %s" %e

    def remove_fe(self):
        """
        Removing Linux driver from the Linux_Host using rpm -e
        """
        try:
            vm=Passh(host=vmHost, username=vmUser, password=vmPass, verbose=VerboseLevel, doReturn=True)
            cmd = 'rpm -qa|grep fedriver'
            stdoutData, stderrData = vm.run_ssh(cmd=cmd)
            if stdoutData and not stderrData:
                ToRemove = stdoutData[0].strip()
                print "rpm -ev %s %s" %(rpmOptions, ToRemove)

                cmd = "rpm -ev %s %s" %(rpmOptions, ToRemove)
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                for line in stdoutData: print line.strip('\n')
                for line in stderrData: print line.strip('\n')
                cmd = 'rpm -qa|grep %s' %ToRemove
                stdoutData, stderrData = vm.run_ssh(cmd=cmd)
                if not stdoutData:
                    print "Removed %s" %ToRemove
                else:
                    print "Error while trying to remove %s" %ToRemove
            else:
                print "Warning: did not find a Linux driver to remove."

            for line in stdoutData: print line.strip('\n')
            for line in stderrData: print line.strip('\n')

        except Exception, e:
            print "Error: %s" %e

#Main
# run as module, or as script
if __name__ == "__main__" and not Inline:

    cmd = ''
    verbose = False 
    rpmOptions = "" 
    VerboseLevel = '0'

    showBuild = False
    query = False 
    update = False 
    erase = False 
    buildNum = None 
    simulate = False

    ERROR = -1

    def usage():
        print "Usage: %s [options]" % (_thisScript)
        print "        -h <Linux_Host> - specify Linux_Host hostname or IP. Also requires -q, -u, or -e." 
        print "    Action. Must specify one of these below:"
        print "        -q - to query for the Linux driver on the Linux_Host."
        print "        -u - to update the Linux driver on the Linux_Host."
        print "        -e - to erase or remove any Linux driver(s) on the Linux_Host."
        print "        -s - to show the builds that are available. supply with -b option to show the Linux drivers for that build."
        print "    Optional arguments:"
        #print "        -t <type> - The build type. Type can be 'official', 'nightly', or 'test'. (Default is 'official')."
        print "        -b <num> - specify the build number, or the word 'latest'. Don't specify the 'type' part, such as 'official'"
        #print "        -g <tag> - (specify this only if type is nightly). Valid arguments are 'beta' or 'trunk'."
        print "        -l <user> - the user on the Linux_Host (default = root)"
        print "        -p <password> - the password of the user on the Linux_Host (default = vmPassword)"
        print "        -x valid with -u option only. Simulate but don't perform the Linux driver update."
        print "        -v <value> - set to 1 for verbose (defauilt = 0)"
        print "        -o <rpm_options> - valid with -u option only. Will pass the 'rpm_options' to the rpm command, unmodified"
        print "Examples:"
        print "    Show available builds:" 
        print "        %s  -s\n" %_thisScript

        print "    Show available files for builds 303:" 
        print "        %s  -s -b 303\n" %_thisScript

        print "    Update Linux driver on Linux_Host:"
        print "        %s  -h 10.48.257.258 -u -b 303\n" %_thisScript

        print "    Update Linux driver on Linux_Host, with rpm options:"
        print "        %s  -h 10.48.257.258 -u -b 303 -o '--force --nodeps' \n" %_thisScript

        print "    Remove Linux drivers on Linux_Host:"
        print "        %s  -h 10.48.257.258 -e\n" %_thisScript

        print "    Query Linux driver on Linux_Host:"
        print "        %s  -h 10.48.257.258 -q" %_thisScript

    argc = len(sys.argv)
    if (argc < 2):
        print "\nThis program queries, updates, and erase Linux drivers on a Linux_Host.\n"
        usage()
        sys.exit(ERROR)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "b:l:p:c:h:o:v:eqsux?",
            ["user=", "password=", "simulate", "show", "query", "erase", "update", 
                "host=", "command=", "build=", "rpm_options=", "verbose="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(ERROR)

    for o, a in opts:
        if o in ("-?", "--help") :
            print "\nThis program queries, updates, and erase Linux drivers on a Linux_Host.\n"
            usage()
            sys.exit(ERROR)
        if o in ("-l", "--user") :
            vmUser= a
        elif o in ("-p", "--password") :
            vmPass = a
        elif o in ("-x", "--simulate") :
            simulate = True 
        elif o in ("-s", "--show") :
            showBuild = True 
        elif o in ("-q", "--query") :
            query = True 
        elif o in ("-e", "--erase") :
            erase = True 
        elif o in ("-u", "--update") :
            update = True 
        elif o in ("-h", "--host") :
            vmHost = a
        elif o in ("-c", "--command") :
            cmd = a
        elif o in ("-b", "--build") :
            buildNum = a
        elif o in ("-o", "--rpm_options") :
            rpmOptions = a
        elif o in ("-v", "--verbose") :
            verbose = True  
            VerboseLevel = '1'
        else:
            assert False, "unhandled option"
            sys.exit(ERROR)

    # if just -h, but no other options, print a notice
    if (vmHost is not None) and (erase is None or update is None or query is None):
        print "\nError: -h <Linux_Host> requires also specifying -e, -q, or -u\n"
        sys.exit(ERROR)

    if (update is True) and (vmHost is None or buildNum is None):
        print "\nError: Update requires at least these three options: -h <Linux_host_or_IP>  -b <build>  -u\n"
        sys.exit(ERROR)

    if (query is True) and (vmHost is None):
        print "\nError: Query requires at least these two options: -h <Linux_host_or_IP> -q\n"
        sys.exit(ERROR)

    if (simulate is True) and (vmHost is None or update is None):
        print "\nError: Update with simulation requires these options: -h <Linux_host_or_IP> -b <build> -u -x\n"
        sys.exit(ERROR)

    if (erase is True) and (vmHost is None):
        print "\nError: Erase requires at least these two options: -h <Linux_host_or_IP>  -e\n"
        sys.exit(ERROR)

    fe = RPMUtil(simulate=simulate)

    if query is True:
        fe.query_fe()
    elif showBuild is True:
        fe.show_fe(buildNum=buildNum)
    elif update is True:
        fe.update_fe(buildNum=buildNum)
    elif erase is True:
        fe.remove_fe()
    else:
        print "\nWarning: Not enough command line imput. Please specify an Action to perform such as -q, -s, -u, or -e.\n"
        usage()
        sys.exit(ERROR)

