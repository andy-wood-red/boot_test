#!/usr/bin/python
# Run a boot test of a Comcast/Sky platform on a local network using a smart switch.

import sys
import requests

from time import sleep
from datetime import datetime, timezone

from paramiko import SSHClient
from scp import SCPClient

import os

import sysd_analyze

# Test unit IP, these will most likely be overridden by parameters passed into the script.
llama_ip = '192.168.0.18'
xione_ip = '192.168.0.171'
switch_ip = '192.168.0.150'
platform_ip = xione_ip

# Number of interations and delay waiting for boot to complete (secs),
# and these are likely to be overridden by parameters passed in.
loops = 1
wait_for_full_boot = 90 # Delay time in secs

# Smart switch API for on and off.
# This is the API for a Shelly switch, others will of course be different.
switch_on = "/rpc/Switch.Set?id=0&on=true"
switch_off = "/rpc/Switch.Set?id=0&on=false"

# Path to local copies of the log files to parse to see if EPG started.
sky_logfile = './logs/sky-messages.log'
sys_logfile = './logs/system.log'
# Location to locally store obtained bootmetrics during this test cycle.
bootmetrics_file = './logs/bootmetrics.txt'

# Use for timestamps etc.
utc_time = datetime.now(timezone.utc)

# Function to ssh into the UUT and obtain log files.
def get_log_files():
    ssh = SSHClient()
    ssh.load_system_host_keys()

    try:
        ssh.connect(platform_ip,10022,'root','')
    except:
        print('Failed to connect to test unit via SSH.')
        return

    # SCPCLient takes a paramiko transport as an argument
    scp = SCPClient(ssh.get_transport())

    # Get the system log.
    # local_filename = utc_time.isoformat() + '_system.log'
    scp.get(remote_path='/opt/logs/system.log',local_path=sys_logfile)
    scp.get(remote_path='/opt/logs/sky-messages.log',local_path=sky_logfile)

    scp.close()
    return

# Function to check for occurrence of log entry that shows EPG is running.
def check_for_epg():
    file = open(sky_logfile,encoding = "ISO-8859-1")
    lines = file.readlines()
    file.close()

    for line in lines:
        if line.find(" app 'com.bskyb.epgui' running") != -1:
            # print('Found the string.')
            return 1
        
    return 0

# Function to turn the smart switch on or off, default to off.
def switch(ip_addr,switch_state):
    # We could print() r.json() to analyze what happened.
    if switch_state == 'on':
        url = "http://" + ip_addr + switch_on
    else:
        url = "http://" + ip_addr + switch_off

    r = requests.get(url)
    return

# Function to parse and store systemd metrics.
def store_metrics(metrics,file_location):
    file = open(file_location,"a")
    if not metrics:
        print('Empty response found.')
    else:
        for metric in metrics:
            file.write(metric + '\n')
    file.close()
    return

# Function to parse and store systemd metrics.
def timestamp_metrics(file_location):
    file = open(file_location,"a")
    utc_time = datetime.now(timezone.utc)
    timestamp_str = utc_time.strftime('------- %Y-%m-%d  %H:%M:%S\n')
    file.write(timestamp_str)
    file.close()
    return

###############################################################################
# Main program starts here

# total arguments
n = len(sys.argv)

# If too few arguments show usage.
if n < 2:
    print("Usage - ./boot_test_loop.py [-s switch_ip_address -t UUT_ip_address -l number_of_iterations -d delay_time in secs]")
    print("  default values are currently: switch_ip_address == ",switch_ip)
    print("                                UUT_ip_address == ",platform_ip)
    print("                                number_of_iterations == ",loops)
    print("                                delay_time == ",wait_for_full_boot)
else:
    i = 1
    while i < n:
        match sys.argv[i]:
            case '-s':
                switch_ip = sys.argv[i+1]
                i += 2
            case '-t':
                platform_ip = sys.argv[i+1]
                i += 2
            case '-l':
                loops = int(sys.argv[i+1])
                i += 2
            case '-d':
                wait_for_full_boot = int(sys.argv[i+1])
                i += 2
            case _:
                i += 1
           
#    print('After parse; switch==',switch_ip,'platform==',platform_ip,'and num of iterations==',loops)

#Before running the test make sure logs folder exists locally.
    if not os.path.exists('./logs'):
        os.makedirs('./logs')

# If an old bootmetrics file exists it will be overwritten.
    file = open(bootmetrics_file,"w")
    utc_time = datetime.now(timezone.utc)
    timestamp_str = utc_time.strftime('======== Test Started %Y-%m-%d  %H:%M:%S ========\n')
    file.write(timestamp_str)
    file.close()


# The test loop
    for x in range(loops):
        utc_time = datetime.now(timezone.utc)
        # Turn on test unit and wait for a short period before seeing whether it booted OK.
        print(utc_time, 'turn on for test loop ', x)
        timestamp_metrics(bootmetrics_file)
        switch(switch_ip,'on')
        sleep(wait_for_full_boot)

        # Get systemd metrics and store them.
        metrics = sysd_analyze.get_systemd_analyze_metrics(platform_ip,'')
        store_metrics(metrics,bootmetrics_file)
        metrics = sysd_analyze.get_system_metric(platform_ip,'cat /opt/logs/sky-messages.log | grep SpectrumBarGadget | grep complete')
        store_metrics(metrics,bootmetrics_file)
        # Get log files and parse for text indicating boot status.
        get_log_files()
        if check_for_epg() == 0:
            print('Log indicates EPG did not start.')
            print('Test unit is still on so logs etc. can be checked manually.')
            exit()
                
        # Turn off and wait a few secs before repeating the process.
        utc_time = datetime.now(timezone.utc)
        print(utc_time, 'turn off for test loop ', x)
        switch(switch_ip,'off')
        sleep(5)
