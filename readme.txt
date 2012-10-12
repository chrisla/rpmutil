summary: 
This program is used to run the rpm command on remote machines.

Do you need to check, remove, or update rpm packages on hundreds of Linux machines?
This program can be used to do just that. It runs the rpm command remotely via ssh.

Dependency: 
This requires the paramiko and Crypto packages to be installed.
Only Linux is supported at this time.

Code path:
rpmutil calls rpmutil.py, which calls passh.py. rpmutil is a shell script. rpmutil.py contains the high level logic, while passh.py contains the low level code needed to perform ssh on remote machines. The python code are written as both a CLI and a library. For example, you can run rpmutil.py from the command line, or you can "import rpmutil" as a class to be used by some other python script.  This is very useful for cases where you need to use rpmutil programatically in a larger automation framework. 

Disclaimer: 
This code is untested and was never put into production. Use at your own risk. 
Also, I had to make some modifications recently and no longer have a Linux environment to test, 
so expect some minor typos, etc.
