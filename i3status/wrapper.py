#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script is a simple wrapper which prefixes each i3status line with custom
# information. It is a python reimplementation of:
# http://code.stapelberg.de/git/i3status/tree/contrib/wrapper.pl
#
# To use it, ensure your ~/.i3status.conf contains this line:
#     output_format = "i3bar"
# in the 'general' section.
# Then, in your ~/.i3/config, use:
#     status_command i3status | ~/i3status/contrib/wrapper.py
# In the 'bar' section.
#
# In its current version it will display the cpu frequency governor, but you
# are free to change it to display whatever you like, see the comment in the
# source code below.
#
# © 2012 Valentin Haenel <valentin.haenel@gmx.de>
#
# This program is free software. It comes without any warranty, to the extent
# permitted by applicable law. You can redistribute it and/or modify it under
# the terms of the Do What The Fuck You Want To Public License (WTFPL), Version
# 2, as published by Sam Hocevar. See http://sam.zoy.org/wtfpl/COPYING for more
# details.

import sys
import json
import subprocess

none = "#FFFFFF"
red = "#ff0000"
yellow = "#ffee00"
green = "#04ff00"
light_blue = "#00ffee"
dark_blue = "#0026ff"
purple = "#f200ff"

bad_color = red
warning_color = yellow
good_color = green


def get_governor():
    """ Get the current governor for cpu0, assuming all CPUs use the same. """
    with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor') as fp:
        return fp.readlines()[0].strip()


# TODO: change color based on time left
def insert_battery(json_data):
    cmd = "acpi"
    output = subprocess.check_output(cmd).strip().decode("utf-8").split()
    battery_status = (output[2] + " " + output[3] +
                      " " + output[4]).replace(",", "")
    battery_status = battery_status.lower()

    color = none
    if output[2] == "Discharging,":
        color = warning_color
        percent = int(output[3][:-2])

        if percent < 20:
            color = bad_color
    elif output[2] == "Charging,":
        color = good_color

    json_data.insert(0, {'full_text': '%s' % battery_status, 'color': color})


def insert_cpu_temp(json_data):
    cpu_temp_str = "cpu_temp: "
    color = none

    cmd = "sensors"
    output = subprocess.check_output(cmd).strip().decode("utf-8")
    for line in output.split("\n"):
        if "temp1" in line:
            temp = line.split()
            cpu_temp_str += temp[1][1:]
            act_temp = int(temp[1][1:-4])

            break

    if act_temp > 100:
        color = bad_color
    elif act_temp > 70:
        color = warning_color
    json_data.insert(0, {'full_text': '%s' % cpu_temp_str, 'color': color})


def insert_fan_rpm(json_data):
    cpu_fan_str = "cpu_fan: "
    color = none

    cmd = "sensors"
    output = subprocess.check_output(cmd).strip().decode("utf-8")

    for line in output.split("\n"):
        if "cpu_fan" in line:
            fan = line.split()
            for f in fan:
                if f.isdigit():
                    cpu_fan_str += f
                    if int(f) > 0:
                        color = bad_color  # but actually good
                    # break
    cpu_fan_str += " rpm"

    json_data.insert(0, {'full_text': '%s' % cpu_fan_str, 'color': color})


def insert_cpu_usage(json_data):
    cpu_fan_str = "cpu_fan: "
    color = none

    last_idle = last_total = 0
    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = 100.0 * (1.0 - idle_delta / total_delta)
    # print('%5.1f%%' % utilisation, end='\r')
    cpu_fan_str += str(utilisation)
    json_data.insert(0, {'full_text': '%s' % cpu_fan_str, 'color': color})


def print_line(message):
    """ Non-buffered printing to stdout. """
    sys.stdout.write(message + '\n')
    sys.stdout.flush()


def read_line():
    """ Interrupted respecting reader for stdin. """
    # try reading a line, removing any extra whitespace
    try:
        line = sys.stdin.readline().strip()
        # i3status sends EOF, or an empty line
        if not line:
            sys.exit(3)
        return line
    # exit on ctrl-c
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    # Skip the first line which contains the version header.
    print_line(read_line())

    # The second line contains the start of the infinite array.
    print_line(read_line())

    while True:
        line, prefix = read_line(), ''
        # ignore comma at start of lines
        if line.startswith(','):
            line, prefix = line[1:], ','

        j = json.loads(line)
        # insert information into the start of the json, but could be anywhere
        # CHANGE THIS LINE TO INSERT SOMETHING ELSE
        insert_battery(j)
        # j.insert(0, {'full_text' : '%s' % get_governor(), 'name' : 'gov', 'color' : '#cb4b16'})
        j.insert(5, {'full_text': ' + ', 'name': 'gov', 'color': green})
        j.insert(0, {'full_text': 'add_wifi and IP',
                     'name': 'gov', 'color': '#FF00FF'})
        j.insert(0, {'full_text': 'wifi speed',
                     'name': 'gov', 'color': '#00FFFF'})

        insert_cpu_temp(j)
        insert_fan_rpm(j)

        insert_cpu_usage(j)
        # j.insert(0, {'full_text' : '%s' % get_battery(), 'name' : 'bat', 'color' : '#F0F0F0'})
        # and echo back new encoded json
        print_line(prefix+json.dumps(j))
