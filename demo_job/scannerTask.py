!$EDGE
#input drone slat slon

import math

alt = 10
length = 50
step = 25
results = 'resfile'
outputDir = 'tmp'

def getNewLat(lat, distance, direction):
	standard_dist = 111111.0
	nlat = lat + (distance / standard_dist)*direction
	return nlat

def getNewLon(lat, lon, distance, direction):
	standard_dist = 111111.0
	rad = (lat * math.pi) / 180
	nlon = lon + (distance/ (standard_dist*(math.cos(rad))))*direction
	return nlon

ofile = open(results, 'w')

logger.info("started")

n = mco.group.getNodeByNameStr(drone) 

n.MobilitySvc.Arm()
logger.info("waiting to arm")
mco.wait([n.MobilitySvc.GetArmedStatus,"==","ARMED"],1,20)

n.MobilitySvc.TakeOff(alt) 
logger.info("waiting to take off")
mco.wait([n.MobilitySvc.getDistanceFromTakeOffAlt,"<",1.0],1,20) 


steps = length/step

logger.info("Going to start point")
#print (y,x)
n.MobilitySvc.GotoWaypoint(slat,slon,10.000000)
#mco.wait([n.MobilitySvc.getAirSpeed,">",0.8],1,300)
mco.wait([n.MobilitySvc.getDistanceFromTarget,"<",1.0],1,300)



wp = n.MobilitySvc.GetCurrentPosition()
lat = wp.get(n.namestr).lat
lon = wp.get(n.namestr).lon

direction = 1
possition = 0
for x in range(0, steps):
    for y in range(0, steps):
        if x == 0 or y != 0: #!(x != 0 and y == 0)
            lat = getNewLat(lat, step, direction)
        #print(lat)
        #print(lon)
        logger.info("Going to new way point")
        #print (y,x)
        n.MobilitySvc.GotoWaypoint(lat,lon,10.000000)
        mco.wait([n.MobilitySvc.getAirSpeed,">",0.8],1,300)
        mco.wait([n.MobilitySvc.getDistanceFromTarget,"<",1.0],1,300)

        logger.info("Taking photo")

        filename = outputDir+"/photo_"+str(possition)
        n.MyCameraSvc.TakePicture(filename)
        
        ofile.write(str(possition)+': '+ str(lat) + ',' + str(lon)+'\n')
        possition = possition + 1

    lon = getNewLon(lat, lon, step, 1)
    direction = -direction
ofile.close()
n.MobilitySvc.Land()
logger.info("waiting to disarm")
mco.wait([n.MobilitySvc.GetArmedStatus,"==","DISARMED"],1,60)


