!$MANAGER
#input inputfile1 inputfile2


ifile = open(f'{inputfile1}/CountResults', 'r')
lines = ifile.readlines()
print("Results for zoneA")
sumdetect = 0
sumofphoto = len(lines) - 2
for i, line in enumerate(lines):
    if i == 0:
        print("Sum of photos:"+ line)
        print(f"In {sumofphoto} of them found at least one object")
        continue
    if i == len(lines) - 1:
        continue
    sumdetect = sumdetect + int(list(line.split(':'))[1])

print(f"Sum of detected objects {sumdetect}")

ifile = open(f'{inputfile2}/CountResults', 'r')
lines = ifile.readlines()
print("Results for zoneB")
sumdetect = 0
sumofphoto = len(lines) - 2
for i, line in enumerate(lines):
    if i == 0:
        print("Sum of photos:"+ line)
        print(f"In {sumofphoto} of them found at least one object")
        continue
    if i == len(lines) - 1:
        continue
    sumdetect = sumdetect + int(list(line.split(':'))[1])

print(f"Sum of detected objects {sumdetect}")



