# Run a systemd-analyze command remotely.

from paramiko import SSHClient
from time import sleep

# Function to ssh into the UUT and obtain systemd-analyze metrics for a specific service.
def get_systemd_analyze_metrics(remote_ip,service):
    ssh = SSHClient()
    ssh.load_system_host_keys()

    try:
        ssh.connect(remote_ip,10022,'root','')
    except:
        print('Failed to connect to test unit via SSH.')
        return

    cmd = 'systemd-analyze ' + service
    stdin ,stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    lines = stdout.readlines()
    ssh.close()
    return lines

# Function to ssh into the UUT and run any system command.
# Returns the cmd response as a list, assuming there may be more than one
# line of text which constitutes the response.
def get_system_metric(remote_ip,cmd):
    ssh = SSHClient()
    ssh.load_system_host_keys()

    try:
        ssh.connect(remote_ip,10022,'root','')
    except:
        print('Failed to connect to test unit via SSH.')
        return

    stdin ,stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    lines = stdout.readlines()
    ssh.close()
    return lines
