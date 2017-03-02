from PIL import Image
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings

# you'll need to get PIL 
# some other (shorter) scripts
# that use PIL:
#   create a thumbnail with PIL  
#   find the average image RGB  
#   replace image colors with PIL  
#
# this script is based on the

#   find the sun script   

class TheOutliner(object):
    ''' takes a dict of xy points and
        draws a rectangle around them '''
    def __init__(self):
        self.outlineColor = 0, 255, 255
        self.pic = None
        self.picn = None
        self.minX = 0
        self.minY = 0
        self.maxX = 0
        self.maxY = 0
        # Enter your storage info here
        self.block_blob_service = BlockBlobService(account_name='myaccount', account_key='mykey')
    def doEverything(self, imgPath, dictPoints, theoutfile):
        self.loadImage(imgPath)
        self.loadBrightPoints(dictPoints)
        self.drawBox()
        self.crop()
        self.saveImg(theoutfile)
    def loadImage(self, imgPath):
        self.pic = Image.open(imgPath)
        self.picn = self.pic.load()
    def loadBrightPoints(self, dictPoints):
        '''iterate through all points and

           gather max/min x/y '''


        # an x from the pool (the max/min
        #   must be from dictPoints)
        self.minX = dictPoints.keys()[0][0]
        self.maxX = self.minX
        self.minY = dictPoints.keys()[0][1]
        self.maxY = self.minY


        for point in dictPoints.keys():
            if point[0] < self.minX:
                self.minX = point[0]
            elif point[0] > self.maxX:
                self.maxX = point[0]

            if point[1]< self.minY:
                self.minY = point[1]
            elif point[1] > self.maxY:
                self.maxY = point[1]
    def drawBox(self):
        # drop box around bright points

        for x in xrange(self.minX, self.maxX):
            # top bar
            self.picn[x, self.minY] = self.outlineColor
            # bottom bar
            self.picn[x, self.maxY] = self.outlineColor
        for y in xrange(self.minY, self.maxY):
            # left bar
            self.picn[self.minX, y] = self.outlineColor
            # right bar
            self.picn[self.maxX, y] = self.outlineColor
    def crop(self, i, filename):
        #print self.minX, self.minY, self.maxX, self.maxY
        self.pic.copy().crop((self.minX, self.minY, self.maxX, self.maxY)).save(filename)
        
        # Save these coordinates to table
        #Top bar
        # self.minX, self.minY
        # self.maxX, self.minY

        #Bottom bar
        # self.minX, self.maxY
        # self.maxX, self.maxY

        #Left bar
        # self.minX, self.minY
        # self.minX, self.maxY

        #Right bar
        # self.maxX, self.minY
        # self.maxX, self.maxY
    def saveImg(self, outFile, path):
        #self.pic.save(theoutfile, "JPEG")
        self.block_blob_service.create_blob_from_path(
            'image-objects/' + path,
            outFile,
            outFile,
            content_settings=ContentSettings(content_type='image/jpg')
                    )



#class CollectBrightPoints(object):
#
#    def __init__(self):

#        self.brightThreshold = 240, 240, 240
#        self.pic = None
#        self.picn = None
#        self.brightDict = {}
#    def loadImage(self, imgPath):
#        self.pic = Image.open(imgPath)
#        self.picn = self.pic.load()
#    def collectBrightPoints(self):
#        for x in xrange(self.pic.size[0]):

#            for y in xrange(self.pic.size[1]):
#                r,g,b = self.picn[x,y]
#                if r > self.brightThreshold[0] and \
#                    g > self.brightThreshold[1] and \
#                    b > self.brightThreshold[2]:
#                    # then it is brighter than our threshold

#                    self.brightDict[x,y] = r,g,b


class ObjectDetector(object):
    ''' returns a list of dicts representing 
        all the objects in the image '''
    def __init__(self):
        self.detail = 4
        self.objects = []
        self.size = 1000
        self.no = 255
        self.close = 100
        self.pic = None
        self.picn = None
        self.brightDict = {}
    def loadImage(self, imgPath):
        self.pic = Image.open(imgPath)
        self.picn = self.pic.load()
        self.picSize = self.pic.size
        self.detail = (self.picSize[0] + self.picSize[1])/700
        self.size = (self.picSize[0] + self.picSize[1])/8
        # each must be at least 1 -- and the larger

        #   the self.detail is the faster the analyzation will be
        self.detail += 1
        self.size += 1
        
    def getSurroundingPoints(self, xy):
        ''' returns list of adjoining point '''
        x = xy[0]
        y = xy[1]
        plist = (
            (x-self.detail, y-self.detail), (x, y-self.detail), (x+self.detail, y-self.detail),
            (x-self.detail, y),(x+self.detail, y),
            (x-self.detail, y+self.detail),(x, y+self.detail),(x+self.detail,y+self.detail)
            )
        return (plist)

    def getRGBFor(self, x, y):
        try:
            return self.picn[x,y]
        except IndexError as e:
            return 255,255,255

    def readyToBeEvaluated(self, xy):
        try:
            r,g,b = self.picn[xy[0],xy[1]]
            if r==255 and g==255 and b==255:
                return False
        except:
            return False
        return True

    def markEvaluated(self, xy):
        try:
            self.picn[xy[0],xy[1]] = self.no, self.no, self.no
        except:
            pass

    def collectAllObjectPoints(self):
        for x in xrange(self.pic.size[0]):
            if x % self.detail == 0:
                for y in xrange(self.pic.size[1]):
                    if y % self.detail == 0:
                        r,g,b = self.picn[x,y]
                        if r == self.no and \
                            g == self.no and \
                            b == self.no:
                            # then no more

                            pass
                        else:
                            ol = {}
                            ol[x,y] = "go"
                            pp = []
                            pp.append((x,y))
                            stillLooking = True
                            while stillLooking:
                                if len(pp) > 0:
                                    xe, ye = pp.pop()
                                    # look for adjoining points

                                    for p in self.getSurroundingPoints((xe,ye)):
                                        if self.readyToBeEvaluated((p[0], p[1])):
                                            r2,g2,b2 = self.getRGBFor(p[0], p[1])
                                            if abs(r-r2) < self.close and \
                                                abs(g-g2) < self.close and \
                                                abs(b-b2) < self.close:
                                                # then its close enough

                                                ol[p[0],p[1]] = "go"
                                                pp.append((p[0],p[1]))

                                            self.markEvaluated((p[0],p[1]))
                                        self.markEvaluated((xe,ye))
                                else:
                                    # done expanding that point
                                    stillLooking = False
                                    if len(ol) > self.size:
                                        self.objects.append(ol)


if __name__ == "__main__":
    print "Start Process"

    # assumes that the .jpg files are in
    #   working directory 
    theFile = "3.jpg"

    theOutFile = "3.output.jpg"

    import os
    os.listdir('.')
    for f in os.listdir('.'):
        if f.find(".jpg") > 0:
            theFile = f
            print "working on " + theFile + "..."

            theOutFile = theFile + ".out.jpg"
            bbb = ObjectDetector()
            bbb.loadImage(theFile)
            print "     analyzing.."
            print "     file dimensions: " + str(bbb.picSize)
            print "        this files object weight: " + str(bbb.size)
            print "        this files analyzation detail: " + str(bbb.detail)
            bbb.collectAllObjectPoints()
            print "     objects detected: " +str(len(bbb.objects))
            drawer = TheOutliner()
            print "     loading and drawing rectangles.."

            drawer.loadImage(theFile)
            for idx,o in enumerate(bbb.objects):
                outFile = os.path.splitext(theFile)[0] + "-" + `idx` + ".jpg"
                drawer.loadBrightPoints(o)
                drawer.crop(idx, outFile)
                #drawer.drawBox()
                drawer.saveImg(outFile, os.path.splitext(theFile)[0])

            #print "saving image..."
            #drawer.saveImg(theOutFile)

            print "Process complete"

#output
#Start Process
#working on A Good Book to Have on Your Shelf.jpg...
#     analyzing..
#     file dimensions: (500, 667)
#        this files object weight: 146
#        this files analyzation detail: 1
#     objects detected: 6
#     loading and drawing rectangles..

#saving image...
#Process complete
#working on bamboo-forest.jpg...
#     analyzing..
#     file dimensions: (640, 480)
#        this files object weight: 141
#        this files analyzation detail: 1
#     objects detected: 68
#     loading and drawing rectangles..

#saving image...
#
# .............. SNIP .... (I had 20 jpeg files in the dir)
#
#working on Family_Photo.jpg...
#     analyzing..
#     file dimensions: (4200, 3300)
#        this files object weight: 938
#        this files analyzation detail: 4

#     objects detected: 20
#     loading and drawing rectangles..
#saving image...
#Process complete
