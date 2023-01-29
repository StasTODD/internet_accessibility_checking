#!/bin/bash

inet_acces_check_file=main.py
inet_acces_check_path=/home/stastodd/projects/internet_accessibility_checking/
inet_acces_check_script_pid=$(ps -axx | grep internet_accessibility_checking | grep main.py | awk '{print $1}')

if [ $inet_acces_check_script_pid ]
  then
    echo "internet accessibility checking script is running, it has pid: $inet_acces_check_script_pid"
  else
    cd $inet_acces_check_path ; ./$inet_acces_check_file
fi