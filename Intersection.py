class Intersection(object):
    def __init__(self, point, streamOne, streamTwo):
        self.point = point
        self.streamOne = streamOne
        self.streamTwo = streamTwo
        self.impact = -1
        self.tribDrainArea = -1
        self.mainDrainArea = -1

    def setImpact(self, givenImpact):
        self.impact = givenImpact