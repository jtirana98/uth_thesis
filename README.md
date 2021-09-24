# Support for Parallel Drone-based Task Execution at Multiple Edge Points

<u> Edge Node side: </u>

Requirements: 
- create a TeCoLa Docker environment. 
- python 2.7

*EdgeServer.py* : It is a TeCoLa mission program that runs the EdgeServer entity. To start a EdgeServer a unique id should be assigned:
 ``` python EdgeServer.py -z|--zone [zoneID] ```

<u> Cloud Side </u>

Requiremets:
- python 3.8.10

Entities:
- Registry.py : without this entity the system fails to start its executions:
``` python.py Registry.py ```.
- FTPServer.py : runs in the background and handles the Edge Server's FTP request during the "file space synchronitation".
    - before execution the space_file/ directory should be already created. 
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
      - python modules (for python 2):
        - sudo pip2 install numpy==1.15.0
        - pip2 install opencv-python==4.2.0.32
        - sudo apt-get install libglib2.0-0
        - sudo apt-get install libSM.so.6
        - sudo apt-get install -y libsm6 libxext6
        - sudo apt-get install -y install -y libxrender-dev
        - sudo apt-get install -y  libxrender-dev
   * aggreagatorTask.py
