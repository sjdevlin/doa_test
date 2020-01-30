#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 16:25:35 2020
@author: dev
"""

"""
A script to test DOA accuracy
"""

import os
import time
from random import randint, choice
import math
import json
import socket
import RPi.GPIO as GPIO

#set stepper parameters
Step_pin = 21
Dir_pin = 20
# set speed of rotation
delay = 0.001

#set up GPIO to drive stepper
GPIO.setmode(GPIO.BCM)
MODE = (14,15,18)
GPIO.setup(MODE, GPIO.OUT)
RESOLUTION = {'Full':(0,0,0),
'Half':(1,0,0),
'1/4':(0,1,0),
'1/8':(1,1,0),
'1/16':(0,0,1),
'1/32':(1,1,1)}
GPIO.output(MODE,RESOLUTION['Full'])
GPIO.setup(Dir_pin, GPIO.OUT)
GPIO.setup(Step_pin, GPIO.OUT)


#function to go to angle
def go_to_location(angle):
    Direction = 1 if angle>0 else 0
    GPIO.output(Dir_pin, Direction)
    step_count = abs(int(angle * 2)) # multiply by 2 for gearing

    for x in range(step_count):
        GPIO.output(Step_pin, GPIO.HIGH)
        time.sleep(delay)
        data = conn.recv(8192)
        conn.send(b'ii\n')
        GPIO.output(Step_pin, GPIO.LOW)
        time.sleep(delay)
#    keep receiving backlogged socket requests so buffer isnt filled
        data = conn.recv(8192)
        conn.send(b'ii\n')


DATA_FOLDER = r"/home/pi/doa_test/audiofiles/play"
os.chdir(DATA_FOLDER)

files = os.listdir(DATA_FOLDER)

#  Open the result file (append date and time number)
timestr = time.strftime("%m%d-%H%M")
speaker_dist = input("Enter speaker distance: ")
testfilename = '/home/pi/doa_test/testresults/testfile_'+timestr+'('+speaker_dist+').txt'
testresultfile = open(testfilename,'w')


# Start LIstening to ODAS client
#noises = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sources = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#remember to put in IP addresses here
#noises.bind(('192.168.1.11', 8081))
#noises.listen(5)
sources.bind(('192.168.1.11', 8080))
sources.listen(5)
conn, addr = sources.accept()
#conn2, addr2 = noises.accept()


old_angle = 0
for i in range (1,10):

#not sure if this is right place for this

    new_angle = randint(-180,180)
    #first reset to zero by sending negative of last angle
    go_to_location(old_angle*-1)
    #then go to new (stops cord getting tangled !)
    print ('Going to angle:' + str(new_angle))
    go_to_location (new_angle)
    old_angle=new_angle
    print ('Angle:' + str(new_angle))
    #now choose a randome audio file from the directory
    random_file = choice(files)
    #parse the meta data from the file name
    filedetails = random_file.split("_")


#   take a break to lose the noise from motor and clear buffer
    perceived_angle = 0
    for i in range (1000):
        data = conn.recv(8192)
        conn.send(b'ii\n')
        time.sleep(0.003)

    #play the audio in the background
    os.system ("mpg321 " + random_file + " &")
    tlength = int(filedetails[2])
#    print ("listening for :" + str(tlength))

    #log when we started playing file
    start = time.time()
    time_now = start

#    start listening while time is length is less than length of

    counter = 0
    new_source = 0
    while ((time_now - start)< (int(filedetails[2])+3)):
        data = conn.recv(8192)
        #data2 = conn2.recv(4096)
        if not data: break
    #    print (data)
        jdata = json.loads(data.decode('utf-8'))

        for source in jdata['src']:
            if source['id']>0:
                if (new_source == 0):
                    new_source = source['id']
                if new_source = source['id']:
                    perceived_angle = perceived_angle + math.atan2(source['y'],source['x'])*180/3.142
                    counter +=1

        conn.send(b'ii\n')
        time_now = time.time()

    if counter > 0:
        perceived_angle = perceived_angle / counter
        print ('Angle:' + str(perceived_angle) + '    Source:' + str(source['id']))
    # write out results
    testresultfile.write("Act Angle:{}, Calc Angle:{}, Age:{}, Sex:{}, Act Length:{}\n".format(new_angle,perceived_angle,filedetails[1],filedetails[0],filedetails[2]) )


go_to_location(old_angle*-1)
GPIO.cleanup()