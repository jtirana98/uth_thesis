'''
It is a mission program, that runs at each edge point.
- Waits for a new task from the TaskManager, runs the task and then
returns the results back
- Spreads, periodically, its info and node-services availabilities 
'''
import sys
import time
import argparse
import threading
from ftplib import FTP
import os
import Pyro4
import re
import shutil
from six import string_types
from tecola.env import tecola_env_conf as env
from tecola.core.mc import MissionController
from tecola.core import TeCoLaExceptions as ex
import logging, logging.handlers

#fix this as in mc
from tecola.core.WP import WP
from tecola.core.DroneStatus import DroneStatus

import socket
import fcntl
import struct
import math

import numpy as np
import time
import cv2
import os


Pyro4.config.SERIALIZER = "json"

#learn my ip
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

__DAY_IN_SECONDS = 60 * 60 * 24


TECOLA_HOME = os.environ.get("TECOLA_HOME")

#declaring the global variables
mco = None
groups = {}
tasks = []
lock_update = threading.Lock()
lock_group = threading.Lock()
timeout = 3
handler = None
zone_id = None
isItRunning = False
ftp = None
current_path = os.path.abspath('.')
logger = None

class Task():
    def __init__(self, task, id, jobID, file_content, pretask_files, pretask_folders):
        self.task = task
        self.id = id
        self.jobID = jobID
        self.file_content = file_content
        self.pretask_files = pretask_files
        self.pretask_folders = pretask_folders

class TaskExecuter(threading.Thread):
    def run(self):
        print "Executor Thread started\n"
        global handler
        global mco
        global groups
        global zone_id
        global current_path
        global global_sharedSpace_meta
        global logger

        #wait for new session-jobs or updates
        #V3: change directory
        while True:
            lock_update.acquire()
            if len(tasks) == 0:
                nextT = None
            else:
                nextT = tasks.pop(0)
            lock_update.release()

            if nextT == None:
                time.sleep(3)
            else:
                isItRunning = True
                print "Runing task: \n"
                os.chdir(current_path+'/'+zone_id)
                completed = True
                try:
                    exec(nextT.task)
                except:
                    completed = False
                    print('Task fail: Going to previous view in the filespace')
                    #going to a previous view
                    (files, folders) = getFileOfContent(current_path, zone_id)
                    for f in folders:
                        if f not in nextT.pretask_folders and (f != 'tmp' or ('/' in perf)):
                            shutil.rmtree(f)
                    os.chdir(current_path)
                    for f in files:
                        if f not in nextT.pretask_files:
                            if os.path.exists(f):
                                os.remove(f)
                    handler.zone_task_terminated(zone_id, nextT.id, nextT.jobID, False)           
                
                if completed:
                    #V3: sync file space with task manager opposite direction me vasi: nextT.file_content
                    (files, folders) = getFileOfContent(current_path, zone_id)
                    for f in folders:
                        if f not in nextT.pretask_folders:
                            ftp.mkd(f)  
                    print('Task completes: Let\'s sync the shared folder')
                    os.chdir(current_path)
                    for f in files:
                        print('checking for file: ' + f)
                        if f not in nextT.pretask_files:
                            print('that is a new file')
                            fp = open(f, 'r')
                            #A new file was created during this process, so I have to upload this file to  server
                            ftp.storbinary('STOR %s' % f, fp)
                            fp.close()
                
                    handler.zone_task_terminated(zone_id, nextT.id, nextT.jobID, True)
                
                isItRunning = False

def getFileOfContent(path, perf):
    file_content = []
    files = os.listdir(path + '/' +perf)
    folders_content = []
    folders_content_s = []
    for f in files:
        if os.path.isfile(path+'/'+perf+'/'+f):
            file_content.append(perf+'/'+f)
        else:
            if f != 'tmp' or ('/' in perf): #task manager dont have permition for this folder
                folders_content_s.append(f)
                folders_content.append(perf+'/'+f)
    for f in folders_content_s:
        (files, folders) = getFileOfContent(path ,perf+'/'+f)
        file_content = file_content + files
        folders_content = folders_content + folders
    
    return (file_content, folders_content)


@Pyro4.expose
class ReceiveRequests():
    def __init__(self):
        pass
    
    def newTask(self,jobID, id, code, input_values_name, input_values, file_content, folders_content):
        global ftp
        print("Received task %d" %id)
        #V3: sync my file space with the one of Task Managers
        print("Sync with the shared file system")
        (myfiles, myfolders) = getFileOfContent(current_path, zone_id)
        myfolder_req = []
        for f in file_content:
            if f not in myfiles:
                myfolder_req.append(f)
        
        for f in folders_content:
            if f not in myfolders:
                os.mkdir(current_path+'/'+f)

        #v3: request from the FTP server the new-modified files
        for f in myfolder_req:
            fhandle = open(f, 'w')
            time.sleep(1)
            ftp.retrbinary('RETR %s' % f, fhandle.write)
            fhandle.close()
        initial = ""
       
        for i in range(0, len(input_values)):
            if isinstance(input_values[i], string_types):
                initial = initial + input_values_name[i] + "=" + input_values[i]+"\n"
            else:
                initial = initial + input_values_name[i] + "=" + str(input_values[i])+"\n"

        code = initial + code
        (pretask_files, pretask_folders) = getFileOfContent(current_path, zone_id)
        lock_update.acquire()
        tasks.append(Task(code, id, jobID, file_content, pretask_files, pretask_folders))
        lock_update.release()
        #print code
    
    def cleanSpace(self):
        print('GOT COMMAND FOR CLEANNING FILE SPACE')

        while isItRunning:
            time.sleep(2)

        lock_update.acquire()
        shutil.rmtree(zone_id, ignore_errors = True)

        os.mkdir(zone_id)
        os.mkdir(zone_id+'/'+'tmp')
        lock_update.release()

def main():
    global zone_id
    parser = argparse.ArgumentParser(description='The Edge point that manages a specific area')
    parser.add_argument('--zone', '-z', dest='zone', action='store', help='The unique id of the zone', required=True)
    parser.add_argument('--debug', '-d', dest='debug', action='store_true', help='Enable the debug mode of the server to be sent to Cloud', required=False)
    args = parser.parse_args()
    
    zone_id = args.zone
    debug = args.debug

    #init phase:
    task_manager_ip = "192.168.2.102"
    registry_ip = "192.168.2.102"
    logger_ip = "192.168.2.102"

    my_ip = get_ip_address('eth0')
    port_reg = 9557
    port_serv = 9559
    port_handler = 9560
    
    global mco
    global handler
    global isItRunning
    global ftp
    global logger

    #V6: logging
    rootLogger = logging.getLogger('')
    if debug:
        rootLogger.setLevel(logging.DEBUG)
    else:
        rootLogger.setLevel(logging.INFO)
    socketHandler = logging.handlers.SocketHandler(logger_ip,
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    rootLogger.addHandler(socketHandler)

    logger = logging.getLogger(zone_id)

    #V3: create a folder inside which lays the shared with the Task manager file space (folder)
    if os.path.exists(zone_id):#it is like a temp folder
        shutil.rmtree(zone_id, ignore_errors = True)

    os.mkdir(zone_id)
    os.mkdir(zone_id+'/'+'tmp')

    #V3: Connect to ftp server   
    ftp = FTP()
    ftp.connect(task_manager_ip, 2121) 
    ftp.login('user','12345')
    #ftp.dir()
    
    #create a deamon which provides a service to the system through which
    #the Task Manager can send a new task
    #I also create a thread which execs every new task
    task_manager = Pyro4.Daemon(host= my_ip ,port=port_serv)
    obj = ReceiveRequests()
    uri = task_manager.register(obj,objectId='RECREQ')
    srv_th= threading.Thread(target=task_manager.requestLoop)
    srv_th.daemon=True
    srv_th.start()

    taskExecuter_thr = TaskExecuter()
    taskExecuter_thr.daemon = True
    taskExecuter_thr.start()

    #create Registry proxy
    register = Pyro4.Proxy("PYRO:REGISTRYMANAGER@"+ registry_ip+":"+str(port_reg))
    handler =  Pyro4.Proxy("PYRO:HANDLERETURN@"+ task_manager_ip+":"+str(port_handler))
    try:
        print "Mission Controller object creation"
        mco = MissionController(2)
    except:
        print "Mission Controller object creation failed"
        os._exit(1)

    #start tecola engine 
    try:
        mco.start()
        print "TeCoLa engine started"
    except:
        print "TeCoLa engine failed"
        os._exit(1)

    k = 0
    while True:
        if k == 7:#renew ftp session
            ftp = FTP()
            ftp.connect(task_manager_ip, 2121) 
            ftp.login('user','12345')
            k = 0
        else:
            k = k + 1
        if not isItRunning:   
            print "Invite nodes (UAVs) to joing the group"
            mco.checkJoin(3)
        
        print "Current group size %d" % mco.group.size
    	registration_msg = "<zone id = '"+ zone_id +"'" + " ip ='"+ my_ip+ "' port = '"+ str(port_serv)+"'>\n"
        for n in mco.group:
            n.MyCameraSvc.defineWorkspace(current_path+'/'+zone_id)
            wp = n.MobilitySvc.GetCurrentPosition()
            lat = wp.get(n.namestr).lat
            lon = wp.get(n.namestr).lon

            registration_msg = registration_msg + " <node name ='" + n.namestr + "' lat ='"+str(lat) +"' lon ='"+str(lon)+"'> \n"
            for svc in n.services:
                registration_msg = registration_msg + "     <service name='" +svc +"'/> \n"
            registration_msg = registration_msg + " </node>\n"
        registration_msg = registration_msg + "</zone>"
        register.registry(str(zone_id),registration_msg)

        print "Registration was sent successfully"

        time.sleep(timeout)

    
if __name__ == '__main__':
    
    main()
