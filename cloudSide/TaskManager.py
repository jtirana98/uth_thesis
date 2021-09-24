'''
Task Manager, through this process programmer can interact with the
system and import tasks to be executed to Edge servers in a transparent way
'''

import threading
import Pyro4
from lxml import etree
import time
import os
import os.path
import math
import shutil

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

Pyro4.config.SERIALIZER = 'json'
PYRO_SERIALIZERS_ACCEPTED='serpent /usr/bin/python3 -Wignore -m Pyro4.naming'
host_name = '192.168.2.102'
port_reg = 9557
port_handler = 9560

registries = {}
lock_registries = threading.Lock()

runningJobs = False
newJob = None
peddingForTasks = {}
lock_tasks = threading.Lock()
jobsIDs = 0
current_path = os.path.abspath('.')
spaceOfFiles = 'space_file' #the name of the directory in which lays the shared file spaces

managerTasks = []
lock_managerTasks = threading.Lock() #where the TaskManager program lays

class NodeInfo:
    def __init__(self, name, services):
        self.name = name
        self.services = services
    
    def addHome(self, lat, lon):
        self.xo = lat
        self.yo = lon

        standard_dist = 111111
        d = 500
        #y1
        rad = (lat * math.pi) / 180
        self.y1 = lon - (d/ (standard_dist*(math.cos(rad))))

        #y2
        self.rad = (lat * math.pi) / 180
        self.y2 = lon + (d/ (standard_dist*(math.cos(rad))))

        #x1
        self.x1 = lat - (d / standard_dist)

        #x2
        self.x2 = lat + (d / standard_dist)

        printMargin = ""

        for i in range(0,5):
            for j in range(0,6):
                if(i == 0):
                    if(j == 0):
                        printMargin = printMargin + 'A-'
                    elif(j == 4):
                        printMargin = printMargin + '-B'
                    else:
                        if(j != 5):
                            printMargin = printMargin + '-'
                elif(i == 4):
                    if(j == 0):
                        printMargin = printMargin + 'C-'
                    elif(j == 4):
                        printMargin = printMargin + '-D'
                    else:
                        if(j != 5):
                            printMargin = printMargin + '-'
                elif(j == 0 or j == 4):
                        if j == 4:
                            printMargin = printMargin + "  "
                        printMargin = printMargin + '|'
                else:
                    if(i != 2 or j != 3):
                        printMargin = printMargin + " "

                if(i == 2 and j == 3):
                    printMargin = printMargin + 'O'

                elif(j == 5):
                    if(i == 0):
                        printMargin = printMargin + '\t A(' + str(self.x1) + ',' + str(self.y1) + ')\n'
                    if(i == 1):
                        printMargin = printMargin + ' B(' + str(self.x2) + ',' + str(self.y1) + ')\n' 
                    if(i == 2):
                        printMargin = printMargin + ' C(' + str(self.x1) + ',' + str(self.y2) + ')\n' 
                    if(i == 3):
                        printMargin = printMargin + ' D(' + str(self.x2) + ',' + str(self.y2) + ')\n' 
                    if(i == 4):
                        printMargin = printMargin + '\t O(' + str(lat) + ',' + str(lon) + ')\n'
                    
        self.printMargin = printMargin

class EdgeInfo:
    def __init__(self, zone_name,ip, zone_port,nodes):
        self.name = zone_name
        self.ip = ip
        self.port = zone_port
        self.nodes = nodes
        self.edge_proxy = None
        self.running = False
        #print(f'{zone_name}here')
    
    def define_proxy(self, edge_proxy):
        self.edge_proxy = edge_proxy

def makereg(message):
    parser = etree.XMLParser(recover = True)
    message = " " + message
    
    root = etree.fromstring(message, parser)
    #root = root.getroot()
    try:
        if(root.tag != 'zone'):
            raise TypeError('Wrong arguments for registration')
        zone_name = root.attrib.get('id')
        if not zone_name:
            raise TypeError('Wrong arguments for registration')
        
        zone_ip = root.attrib.get('ip')
        if not zone_ip:
            raise TypeError('Wrong arguments for registration')
        zone_port = root.attrib.get('port')
        if not zone_ip:
            raise TypeError('Wrong arguments for registration')

        #get nodes
        nodes = []
        i = 0
        for node in root:
            if node.tag != 'node':
                raise TypeError('Wrong arguments for registration')
            node_name = node.attrib.get('name')
            
            
            lat = float(node.attrib.get('lat'))
            lon = float(node.attrib.get('lon'))

            if not node_name:
                raise TypeError('Wrong arguments for registration');
            #print(node_name)
            services = []
            for srv in node:
                if srv.tag != 'service':
                    raise TypeError('Wrong arguments for registration');
                serv_name = srv.attrib.get('name')
                if not node_name:
                    raise TypeError('Wrong arguments for registration');
                #print(serv_name)
                services.append(serv_name)
            n_node = NodeInfo(node_name, services)
            n_node.addHome(lat, lon)
            nodes.append(n_node)
        
        newEdge = EdgeInfo(zone_name, zone_ip, zone_port,nodes)
        if registries.get(zone_name) == None:
            #V3: create new folder for this zone 
            #if there is already a folder for this zone it has to be reset
            print(f'I will update the file space because of {zone_name}')
            
            os.chdir(current_path + '/' + spaceOfFiles)
            if os.path.exists(zone_name):
               # print(f'There was already a folder fot this zone, lets delete it :)')
                shutil.rmtree(zone_name, ignore_errors = True)
            os.mkdir(zone_name)
            os.chdir(current_path)
        str_i = "PYRO:RECREQ@"+ zone_ip+":"+zone_port
        newEdge.define_proxy(Pyro4.Proxy(str_i))
        
        if zone_name not in registries.keys():
            newEdge.running = False
        else:
            newEdge.running = registries.get(zone_name).running
            #print(f'{newEdge.running} to swsame')
        registries.update({zone_name:newEdge})

    except TypeError as err:
        print (err.args)

class zoneRunning():
    def __init__(self, id):
        self.id = id
        self.started = False
        self.terminated = False
        self.failed = False

    def started(self):
        self.started = True

    def terminated(self):
        self.terminated

def getFileOfContent(path, perf):
    file_content = []
    files = os.listdir(f'{path}/{perf}')
    folders_content = []
    folders_content_s = []

    for f in files:
        if os.path.isfile(f'{path}/{perf}/{f}'):
            file_content.append(f'{perf}/{f}')
        else:
            folders_content_s.append(f'{f}')
            folders_content.append(f'{perf}/{f}')

    for f in folders_content_s:
        (files, folders) = getFileOfContent(path ,f'{perf}/{f}')
        file_content = file_content + files
        folders_content = folders_content + folders

    return (file_content, folders_content)

def checkIfBlocks(z, newJob, id):
    for task in newJob.syncZones.keys():
        #print(task)
        #print(id)
        if id < task:
            if z in newJob.syncZones.get(task):
                return True
    return False

def spreadTasks(task, zone_id, status):
    global runningJobs
    global peddingForTasks
    global newJob
    lock_registries.acquire()
    if zone_id != None:
        if task.types == 2:
            for z in zone_id:
                reg = registries.get(z)
                if reg == None or (not status):
                    runningJobs  = False
                    peddingForTasks = {}
                    newJob = None
                    for reg in registries.keys():
                        registries.get(reg).running = False
                    lock_registries.release()
                    print(f'{bcolors.OKCYAN}Job:{jobsIDs - 1} stoppded because {z} failed{bcolors.ENDC}')
                    return -1
                reg.running = False
            task.done = True
        else:
            if status:
                task.terminatedIN(zone_id)
                reg = registries.get(zone_id)
                if reg != None:
                    reg.running = False
                    #print(f'ok1 {zone_id}')
                if task.terminatedAll():
                    #print('here')
                    task.done = True
            else:
                task.markFailed(zone_id)
                reg = registries.get(zone_id)
                if reg != None:
                    reg.running = False
                if task.terminatedAll():
                    task.done = True
                if checkIfBlocks(zone_id, newJob, task.id):
                    runningJobs  = False
                    peddingForTasks = {}
                    newJob = None
                    for reg in registries.keys():
                        registries.get(reg).running = False
                    lock_registries.release()
                    print(f'{bcolors.FAIL}Job:{jobsIDs - 1} stoppded because {zone_id} failed{bcolors.ENDC}')
                    return -1
   
    if task.types == 2 and zone_id == None:
        #the first task of the job is a sync task
        list_of_them = ""
        for z in task.zones:
            reg = registries.get(z)
            
            if reg == None:
                runningJobs  = False
                peddingForTasks = {}
                newJob = None
                for reg in registries.keys():
                    registries.get(reg).running = False
                lock_registries.release()
                print(f'{bcolors.OKCYAN}Job:{jobsIDs - 1} stoppded because {z} failed{bcolors.ENDC}')
                return -1

            reg.running = True
            list_of_them = list_of_them + z + " "
        task.started = True
        lock_registries.release()
        gtask = ManagerTask(task, task.zones)
        print(f"{bcolors.OKCYAN}Sync Task %d send to zones %s {bcolors.ENDC}" %(task.id, list_of_them))
        
        lock_managerTasks.acquire()
        managerTasks.append(gtask)
        lock_managerTasks.release()
        peddingForTasks.update({list_of_them:task})
        return 1
    elif task.types == 2:
        #returned from a sync task
        task.started = False
        task.terminated = True
        task = task.nextTask
        if task == None:
            lock_registries.release()
            return 0 #reached the end
    while True:
        if task.types != 2:
            zones = task.zonesHaveNOTstarted()
            #print(zones)
            for z in zones:
                #check if they are running
                reg = registries.get(z)
                if reg == None:
                    #this registry does not exist
                    if checkIfBlocks(z, newJob, task.id):
                        runningJobs  = False
                        peddingForTasks = {}
                        newJob = None
                        for reg in registries.keys():
                            registries.get(reg).running = False
                        lock_registries.release()
                        print(f'{bcolors.FAIL}Job:{jobsIDs - 1} stoppded because {z} failed{bcolors.ENDC}')
                        return -1
                    else:
                        task.markFailed(z)
                        print(f'{bcolors.FAIL}Failed to send task {task.id} to zone {z}{bcolors.ENDC}')
                        if task.terminatedAll():
                            task.done = True
                        continue
                #print(z)   
                if reg.running == True:
                    continue
                #print('giati')
                #V3: Sync the zone with my space file
                
                path = f'{current_path}/{spaceOfFiles}'
                files = os.listdir(path) #I have the names of the files
                (file_content, folders_content) =  getFileOfContent(path, z)    
                #print(folders_content)
                print(f'{bcolors.OKCYAN}I want to sync my file space with {z} so sending content of file space{bcolors.ENDC}')
                print(f'{bcolors.OKCYAN}Start sending task to edge{bcolors.ENDC}')
                try:    
                    reg.edge_proxy.newTask(task.jobID, task.id, task.code, task.input_values, task.list_of_input.get(z) , file_content, folders_content)
                except:
                    if checkIfBlocks(z, newJob, task.id):
                        runningJobs  = False
                        peddingForTasks = {}
                        newJob = None
                        for reg in registries.keys():
                            registries.get(reg).running = False
                        lock_registries.release()
                        print(f'{bcolors.OKCYAN}Job:{jobsIDs - 1} stoppded because {z} failed{bcolors.ENDC}')
                        return -1
                    else:
                        print(f'{bcolors.FAIL}Zone {z} failed to complete task {task.id}{bcolors.ENDC}')
                        reg.running = False
                        task.markFailed(z)
                        if task.terminatedAll():
                            task.done = True
                        continue
                reg.running = True
                task.startedIN(z)
                
                print(f'{bcolors.OKCYAN}Task {task.id} send to {z}{bcolors.ENDC}')
                peddingForTasks.update({reg.name:task})
            
            task = task.nextTask
            if task == None:
                lock_registries.release()
                return len(peddingForTasks)
            if task.types == 2:
                if not task.allprvDone():
                    lock_registries.release()
                    return len(peddingForTasks)
        else:
            zones = task.zones
            list_of_them = ''
            #check no one of them is running
            for z in task.zones:
                reg = registries.get(z)
                
                if reg == None:
                    runningJobs  = False
                    peddingForTasks = {}
                    newJob = None
                    for reg in registries.keys():
                        registries.get(reg).running = False
                    lock_registries.release()
                    print(f'{bcolors.FAIL}Job:{jobsIDs - 1} stoppded because {z} failed{bcolors.ENDC}')
                    return -1

                if reg.running == True:
                    lock_registries.release()
                    return len(peddingForTasks)
                reg.running = True
                list_of_them = list_of_them + z + ' '
            gtask = ManagerTask(task, task.zones)
            task.started = True
            
            lock_managerTasks.acquire()
            managerTasks.append(gtask)
            lock_managerTasks.release()
            peddingForTasks.update({list_of_them:task})
            print(f'{bcolors.OKCYAN}Sync Task {task.id} send to zones {list_of_them} {bcolors.ENDC}')
            lock_registries.release()
            return len(peddingForTasks)

class Task():
    def __init__(self, id, code, zones, types, input_variables, list_of_input, jobID):
        self.id = id
        self.code = code
        self.nextTask = None
        self.jobID = jobID
        #type == 1 edge addressed
        #type == 2 manager addressed global
        self.types = types
        self.done = False
        if self.types == 2:
            self.terminated = False
            self.started = False
            self.input_values = input_variables
            self.list_of_input = list_of_input
            self.zones = zones #just a list in this case
        else:
            self.input_values = input_variables
            self.list_of_input = list_of_input
            self.zones = {}
            for z in zones:
                rzone = zoneRunning(z)
                self.zones.update({z:rzone})
    
    def defineNext(self, nextTask):
        self.nextTask = nextTask

    #return zones that have not received the task
    def zonesHaveNOTstarted(self):
        rvalue = []
        for z in self.zones.keys():
            if self.zones.get(z).started == False and self.zones.get(z).terminated == False:
                rvalue.append(z)
        return(rvalue)
    
    #return if sync process can start
    def allprvDone(self):
        tasks = newJob.getAllTasks()
        t = tasks[0]
        i = 1
        while t.id != self.id:
            if t.done == False:
                return False
            
            t = tasks[i]
            i = i+1
        return True
    
    #return the zones where the task have started but not terminated
    def zonesStarted(self):
        rvalue = []
        for z in self.zones.keys():
            if self.zones.get(z).started == True and self.zones.get(z).terminated == False:
                rvalue.append(z)
        return(rvalue)
    
    #return the zones where the task have been terminated
    def zonesHaveTerminated(self):
        rvalue = []
        for z in self.zones.keys():
            if self.zones.get(z).terminated == True:
                rvalue.append(z)
        return(rvalue)

    def terminatedAll(self):
        r = self.zonesHaveTerminated()
        for z in self.zones.keys():
            if registries.get(z) == None:
                continue
            if z not in r:
                return False
        return True

    def startedIN(self, id):
        self.zones.get(id).started = True

    def terminatedIN(self, id):
        self.zones.get(id).terminated = True
        self.zones.get(id).started = False
    
    def markFailed(self, id):
        self.zones.get(id).failed = True
        self.zones.get(id).terminated = True
        self.zones.get(id).started = False

class Job():
    def __init__(self, id):
        self.id =id
        self.running = False
        self.task = None
        self.syncZones = {}
    def addTask(self, task):
        self.task = task
    
    def getAllTasks(self):
        alltasks = []
        cur = self.task
        while cur != None:
            alltasks.append(cur)
            cur = cur.nextTask
        return alltasks
    
    def getTask(self, id):
        return(self.getAllTasks()[int(id)])

    def started(self):
        self.running = True
    
    def updateSync(self, taskid, zones):
        self.syncZones.update({taskid:zones})

class UpdateRegistries(threading.Thread):
    def run(self):
        global runningJobs
        global newJob
        global peddingForTasks
        global jobsIDs
        timeout = 10
        update  = Pyro4.Proxy(f'PYRO:REGISTRYMANAGER@{host_name}:{port_reg}')
        prv_values = {}

        terminator = HandleReturn()

        while True:
            values = update.getAll()
            values = list(values.split('-'))
            new_values = []

            for i in range(1, len(values)):
                zone = list(values[i].split(' '))[0]
                st = values[i].find('<')
                regmsg = values[i][st:]
                
                if(prv_values.get(zone) == regmsg):#zone have already been registered and there is no change
                    new_values.append(zone)
                    continue
                
                new_values.append(zone)
                prv_values.update({zone:regmsg})
                #update the registries
                lock_registries.acquire()
                makereg(regmsg)
                lock_registries.release()
            
            k = list(prv_values.keys())
            lock_registries.acquire()

            toTerm = []
            for i in range(0,len(prv_values)):
                z = k[i]
                if z not in new_values:
                    #this zone does not exist anymore
                    registries.pop(z)
                    prv_values.pop(z)
                    
                    taskR = peddingForTasks.get(z)
                    if taskR != None:
                        taskR.markFailed(z)
                        if taskR.terminatedAll():
                            taskR.done = True
                        if checkIfBlocks(z, newJob, taskR.id):
                            #terminate JOB
                            runningJobs  = False
                            for reg in registries.keys():
                                registries.get(reg).running = False
                                #print(f'{z} edw')
                            peddingForTasks = {}
                            newJob = None
                            jobsIDs = jobsIDs + 1
                            print(f'{bcolors.OKCYAN}Job:{jobsIDs - 1} ' \
                                f'stoppded because {z} failed{bcolors.ENDC}')
                        else:
                            toTerm.append((z, taskR))
            lock_registries.release()
            
            for t in toTerm:
                terminator.zone_task_terminated(t[0], t[1].id, t[1].jobID, False)
                #print(f'{t[0]}, {t[1].id}')
            time.sleep(timeout)

class ManagerTask():
    def __init__(self, task, zone):
        self.task = task
        self.zone = zone

class execMabagerCode(threading.Thread):
    def run(self):
        nextT = None
        theProxy = HandleReturn()
        while True:
            lock_managerTasks.acquire()
            if len(managerTasks) == 0:
                nextT = None
            else:
                nextT = managerTasks.pop(0)
            lock_managerTasks.release()
            
            if nextT == None:
                time.sleep(3)
            else:
                runGlobalCode(nextT, theProxy)

def runGlobalCode(newTask, theProxy):
    lock_registries.acquire()
    initiate = ''
    #print(len(newTask.task.input_values))
    for i in range(0, len(newTask.task.input_values)):
        initiate  = initiate + newTask.task.input_values[i] + "=" +  newTask.task.list_of_input[i] + '\n'
    
    #print(initiate)
    #V3: CHANGE DIRECTORY
    #print(f'Starting the execution of manager task {time.time()}')
    os.chdir(current_path+'/'+spaceOfFiles)
    status = True
    try:    
        exec(initiate + newTask.task.code)
    except:
        status = False

    os.chdir(current_path)
    lock_registries.release()
    
    list_of_them = ''
    for z in newTask.task.zones:
        list_of_them = list_of_them + z + ' '

    theProxy.zone_task_terminated(list_of_them, newTask.task.id, newTask.task.jobID, status)


@Pyro4.expose
class HandleReturn():
    def __init__(sefl):
        pass

    def zone_task_terminated(self, zone, taskID, jobID, status):
        global runningJobs
        if runningJobs == False or (jobID != jobsIDs): #job was stoped
            zones = list(zone.split(' '))
            #print(zones)
            for z in zones:
                reg = registries.get(z)
                if reg != None:
                    reg.running = False
                    #print('kalispera')
            return
        if status:
            print(f'{bcolors.OKCYAN}Task returned zone:{zone} task:{taskID} successfully{bcolors.ENDC}')
        else:
            print(f'{bcolors.FAIL}Task returned zone:{zone} task:{taskID} unsuccessfully{bcolors.ENDC}')
        
        mytask = peddingForTasks.get(zone)
        if mytask == None or (mytask.jobID != jobID and mytask.id != taskID):
            return
        peddingForTasks.pop(zone)
        if mytask.types != 2:
            res = spreadTasks(mytask, zone, status)
        else:
            res = spreadTasks(mytask, mytask.zones, status)
        if res == 0:
            print(f'{bcolors.OKCYAN}Job:{jobID} terminated successfully!{bcolors.ENDC}')
            runningJobs = False

class TaskManager():
    started = False

    def __init__(self):
        if not TaskManager.started:
            TaskManager.started = True

        #V3: reset the content of the space folder
        files = os.listdir(current_path + '/' + spaceOfFiles)
        for file in files:
            if os.path.isdir(current_path + '/' + spaceOfFiles + '/' + file):
                shutil.rmtree(current_path + '/' + spaceOfFiles + '/' + file, ignore_errors = True)
            else:
                os.remove(current_path + '/' + spaceOfFiles + '/' + file)
        
        regupdate = UpdateRegistries()
        regupdate.deamon = True
        regupdate.start()

        execMngr = execMabagerCode()
        execMngr.deamon = True
        execMngr.start()

        hadle_return = Pyro4.Daemon(host= host_name ,port=port_handler)
        obj = HandleReturn()
        uri = hadle_return.register(obj,objectId='HANDLERETURN')
        srv_th= threading.Thread(target=hadle_return.requestLoop)
        srv_th.daemon=True
        srv_th.start()

        print(f"{bcolors.UNDERLINE}Actions:{bcolors.ENDC}")
        print(f"{bcolors.HEADER}>list [<zone>] or *\n"\
                        ">run taskEdge@[zone<argas,...>;..] | taskMan@[zone;..]<args,...>\n"\
                        ">stat\n"\
                        ">reset [<zone>] or *\n" \
                        f">kill{bcolors.ENDC}")
        global jobsIDs
        global runningJobs
        global newJob
        global peddingForTasks
        while True:
            cmd=input(f"{bcolors.OKGREEN}$:{bcolors.ENDC}")
            cmd = list(cmd.split(' '))
            if cmd[0] == 'list':
                if len(cmd) == 1:
                    continue
                lock_registries.acquire()
                if cmd[1] == '*': #print them all
                    keys = registries.keys()
                    for k in keys:
                        print(f"{bcolors.OKGREEN}zone: %s{bcolors.ENDC}" %k)
                        edges = registries.get(k)
                        for n in edges.nodes:
                            print(f"{bcolors.UNDERLINE}node: %s{bcolors.ENDC}" % n.name)
                            print(n.printMargin)
                            print(f"{bcolors.BOLD}services: {bcolors.ENDC}")
                            for s in n.services:
                                print("\t " + s + " ")
                else:
                    for i in range(1, len(cmd)):
                        reg = registries.get(cmd[i])
                        if reg == None:
                            print(f"{bcolors.FAIL}no registry for zone: %s {bcolors.ENDC}" %cmd[i])    
                            continue
                        print(f"{bcolors.OKGREEN}zone: %s{bcolors.ENDC}" %cmd[i])
                        edges = registries.get(cmd[i])
                        for n in edges.nodes:
                            print(f"{bcolors.UNDERLINE}node: %s{bcolors.ENDC}" % n.name)
                            print(n.printMargin)
                            print(f"{bcolors.BOLD}services: {bcolors.ENDC}")
                            for s in n.services:
                                print("\t " + s + " ")
                lock_registries.release()
            elif cmd[0] == 'run':
                #create the job and the chain of tasks
                if runningJobs == True:
                    print(f"{bcolors.FAIL}There is another job running{bcolors.ENDC}")
                    continue
                peddingForTasks = {}
                runningJobs = True
                print(f'{bcolors.OKCYAN}Job starts{bcolors.ENDC}')
                jobsIDs = jobsIDs + 1
                newJob = Job(jobsIDs)
                prev_task = None
                id = 0
                ok = 0
                for i in range(1, len(cmd), 2):
                    cmd_ = list(cmd[i].split('@'))
                    task_name  = cmd_[0]
                    task_zones_inputs = cmd_[1]
                    task_id = id = id + 1
                    
                    task_zones_inputs = list(task_zones_inputs[1:len(task_zones_inputs)-1].split(';'))

                    #copy code
                    if not os.path.exists(task_name):
                        print(f"{bcolors.FAIL}There is no task file %s{bcolors.ENDC}"%task_name)
                        ok = -1
                        break
                    
                    f = open(task_name, "r")
                    code = f.read()
                    f.close()
                    parts = list(code.split('\n'))
                    task = None
                    while '' in parts:
                        parts.remove('')
                    #find the type of the code
                    types = parts[0]

                    if types == '!$EDGE':#edge addressed
                        task_zones = []
                        input_forEachZone = {}
                        types = 1
                        for zone in task_zones_inputs:
                            if '<' in zone:
                                zone_ = list(zone.split('<'))
                                task_zones.append(zone_[0])
                                list_of_input = list(zone_[1][0:len(zone_[1])-1].split(','))
                                input_forEachZone.update({zone_[0]:list_of_input})
                            else:
                                task_zones.append(zone)
                                input_forEachZone.update({zone:[]})
                        inputs = list(parts[1].split(' '))[1:] #create a list of inputs name var
                    
                        code = ''
                        for l in range(2,len(parts)):
                            code = code + '\n' + parts[l]
                        task = Task(task_id, code, task_zones, types, inputs, input_forEachZone, jobsIDs)
                    else:#manager addressed
                        types = 2
                        task_zones = task_zones_inputs[0:-1]
                        if '<' in task_zones_inputs[-1]:
                            break_str = list(task_zones_inputs[-1].split(']'))
                            task_zones.append(break_str[0])
                            inputs = list(break_str[1][1:].split(','))
                        else:
                            inputs = []
                            task_zones.append(task_zones_inputs[-1][0:])
                        newJob.updateSync(task_id ,task_zones)
                        input_values = list(parts[1].split(' '))[1:]
                        code = ''
                        for l in range(2,len(parts)):
                            code = code + '\n' + parts[l]
                        task = Task(task_id, code, task_zones, types, input_values, inputs, jobsIDs)
                    #add task to list
                    if i == 1:
                        newJob.addTask(task)
                    else:
                        #append to chain
                        prev_task.defineNext(task)

                    prev_task = task
                if ok == -1:
                    runningJobs = False
                    continue

                if newJob.task == None:
                    newJob.addTask(task)

                #lock_tasks.acquire()
                res = spreadTasks(newJob.task, None, True)
                if res != -1:
                    print(f"{bcolors.OKCYAN}Job %d started{bcolors.ENDC}" %jobsIDs)
                if res == 0 or res == -1:
                    print(f"{bcolors.FAIL}Job %d stopped{bcolors.ENDC}" %jobsIDs)
                    runningJobs = False

                
                #lock_tasks.release()
            elif cmd[0] == 'stat':
                if runningJobs:
                    tasks = newJob.getAllTasks()
                    print(f"{bcolors.OKGREEN}The job: [%d] is running{bcolors.ENDC}" %newJob.id)
                    taskNum = 1
                    lock_registries.acquire()
                    for task in tasks:
                        str_print = "task"+str(taskNum)+": "
                        if task.types == 2:
                            str_print = str_print + "("
                            k = 0
                            for zone in task.zones:
                                if k == len(task.zones) - 1:
                                    str_print = str_print + zone +")"
                                else:
                                    str_print = str_print + zone + ","
                                k = k + 1
                            if task.terminated == False and task.started == False:
                                str_print = str_print + " PENDING"
                            elif task.terminated == False and task.started == True:
                                str_print = str_print + " RUNNING"
                            else:
                                str_print = str_print + " DONE"
                        else:
                            #print(task.zones.keys())
                            for zone in task.zones.keys():
                                if registries.get(zone) == None:
                                   str_print = str_print + zone +": ZONE CRASHED "
                                elif task.zones.get(zone).failed == True:
                                    str_print = str_print + zone +": FAILED "
                                elif task.zones.get(zone).started == False and task.zones.get(zone).terminated == False:
                                    str_print = str_print + zone +": PENDING "
                                elif task.zones.get(zone).started == True and task.zones.get(zone).terminated == False:
                                    str_print = str_print + zone +": RUNNING "
                                else:
                                    str_print = str_print + zone +": DONE "
                        taskNum = taskNum + 1

                        print(str_print)
                    lock_registries.release()
                else:
                    print(f"{bcolors.FAIL}No job is running{bcolors.ENDC}")
            elif cmd[0] == 'kill':
                runningJobs  = False
                peddingForTasks = {}
                newJob = None
                for reg in registries.keys():
                    registries.get(reg).running = False
                time.sleep(1)
                jobsIDs = jobsIDs + 1
                
                print(f'{bcolors.OKCYAN}Job:{jobsIDs - 1} stoppded{bcolors.ENDC}')
            elif cmd[0] == 'reset':
                if len(cmd) == 1:
                    continue
                if runningJobs:
                    print(f"{bcolors.FAIL}There is a job running{bcolors.ENDC}")
                    continue
                lock_registries.acquire()
                if cmd[1] == '*': #print them all
                    keys = registries.keys()
                else:
                    keys = cmd[1:len(cmd)]

                for z in keys:
                    reg = registries.get(z)
                    if reg == None:
                        continue
                    
                    try:    
                        reg.edge_proxy.cleanSpace()
                    except:
                       pass

                    shutil.rmtree(f'{current_path}/{spaceOfFiles}/{z}', ignore_errors = True)
                    os.mkdir(f'{current_path}/{spaceOfFiles}/{z}')                    

                lock_registries.release()
            else:
                print(f"{bcolors.FAIL}wrong input!{bcolors.ENDC}")
                print(f"{bcolors.UNDERLINE}Actions:{bcolors.ENDC}")
                print(f"{bcolors.HEADER}>list [<zone>] or *\n>get <zone>.<variable name>\n"\
                        ">run taskEdge@[zone<argas,...>;..] | taskMan@[zone;..]<args,...>\n"\
                        ">stat\n"\
                        ">reset [<zone>] or *\n" \
                        ">kill"\
                        f"{bcolors.ENDC}")
manager = TaskManager()

while True:
    pass