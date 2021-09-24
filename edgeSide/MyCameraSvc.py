import os
import shutil

class MyCameraSvc:
    def __init__(self, param):
        self.myFiles = '/home/mee/tecola/missions/images'
        self.listOfPhotos = os.listdir(self.myFiles)
        self.current = 0
    
    def defineWorkspace(self, filePath):
        self.destination = filePath
    
    def TakePicture(self, target):
        photo = self.listOfPhotos[self.current]
        self.current = (self.current + 1) % len(self.listOfPhotos)
        
        try:
            shutil.copy(self.myFiles+'/'+photo, self.destination + '/' + target)
        except IOError as e:
            return 'FAILURE'
       
        return 'SUCCESS'
       
