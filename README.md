# Support for Parallel Drone-based Task Execution at Multiple Edge Points

<u> Edge Node side: </u>

Requirements: 
- create a TeCoLa Docker environment. 
- python 2.7

*EdgeServer.py* : It is a TeCoLa mission program that runs the EdgeServer entity. To start a EdgeServer a unique id should be assigned:
 ``` python EdgeServer.py -z|--zone [zoneID] ```

<u> Cloud Side </u>

Requiremets:
- python 3.? 

Entities:
- Registry.py : without this entity the system fails to start its executions:
``` python.py Registry.py ```.
- FTPServer.py : runs in the background and handles the Edge Server's FTP request during the "file space synchronitation".
    - before execution the File_space/ directory should be already created. 
 ``` python.py FTPServer.py ```.
 - LogServer.py : runs in the background, accepts Edge Server's messages through a TCP connection.
  ``` python.py LogServer.py ```.
 - TaskManager.py : provides the command-line interface to user.
  ``` python.py LogServer.py ```.
  
  <u> User - Commands </u>
  > $ list [ \<zone-id\>| \* ]
  > 
  > $ reset  [ \<zone-id\>| \* ]
  >
  > $ kill
  > 
  > $ stat
  >
  > $ run \<edgeTask\>@[zone1<arg1,arg2,..>;..] | ... | \<managerTask\>@[zone1;..]<arg1,arg2..>

  <u> Demo Job </u>
  In the demo_job directory, there is an example of a pipeline of tasks:
  * scannerTask.py drone task for scanning a rectangle
  * detectorTask.py: 
      - *requires the configuration files from demo_job/config. that belongs to [yolo-real-time-object-detection](https://pjreddie.com/darknet/yolo/)*
      - python modules:
         - numpy..  
  * aggreagatorTask.py
