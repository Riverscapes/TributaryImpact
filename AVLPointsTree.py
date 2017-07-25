class PointNode:
    def __init__(self, value, stream=None):
        self.value = value
        self.stream = stream
        self.balanceFactor = 0
        self.left = None
        self.right = None
        self.parent = None

    def __lt__(self, other):
        if isinstance(other, PointNode):
            if float(self.value.X) == float(other.value.X):
                return float(self.value.Y) < float(other.value.Y)
            else:
                return float(self.value.X) < float(other.value.X)
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, PointNode):
            if float(self.value.X) == float(other.value.X):
                return float(self.value.Y) > float(other.value.Y)
            else:
                return float(self.value.X) > float(other.value.X)
        else:
            return NotImplemented

    def __eq__(self, other): #includes buffer region
        if isinstance(other, PointNode):
            x1 = float(self.value.X)
            x2 = float(other.value.X)
            y1 = float(self.value.Y)
            y2 = float(other.value.Y)
            buf = .01
            if (x2 - buf) < x1 < (x2 + buf):
                return (y2 - buf) < y1  < (y2 + buf)
            else:
                return False
        else:
            return NotImplemented

"""Currently not AVL, I'd like to add that in the future"""
class AVLPointsTree:
    def __init__(self):
        self.root = None

    def addNode(self, givenPoint, givenStream):
        newNode = PointNode(givenPoint, givenStream)
        if self.root is None:
            self.root = newNode
        else:
            self.addNodeRecursive(newNode, self.root)

    def addNodeRecursive(self, givenNode, currentNode):
        if currentNode < givenNode:
            if currentNode.right is not None:
                self.addNodeRecursive(givenNode, currentNode.right)
            else:
                currentNode.right = givenNode
                givenNode.parent = currentNode
                self.updateBalance(currentNode.right)
        else:
            if currentNode.left is not None:
                self.addNodeRecursive(givenNode, currentNode.left)
            else:
                currentNode.left = givenNode
                givenNode.parent = currentNode
                self.updateBalance(currentNode.left)


    def findPoint(self, givenValue):
        newNode = PointNode(givenValue)
        return self.findPointRecursive(newNode, self.root)

    def findPointRecursive(self, givenNode, currentNode):
        if currentNode is None:
            return None
        elif currentNode == givenNode:
            return currentNode
        elif currentNode > givenNode:
            return self.findPointRecursive(givenNode, currentNode.left)
        else:
            return self.findPointRecursive(givenNode, currentNode.right)


    def getSize(self):
        if self.root is None:
            return 0
        return self.getSizeRecursive(self.root.left) + self.getSizeRecursive(self.root.right) + 1

    def getSizeRecursive(self, givenNode):
        if givenNode is None:
            return 0
        else:
            return self.getSizeRecursive(givenNode.left) + self.getSizeRecursive(givenNode.right) + 1


    def getHeight(self):
        if self.root is None:
            return 0
        else:
            return max(self.getHeightRecursive(self.root.left), self.getHeightRecursive(self.root.right)) + 1

    def getHeightRecursive(self, currentNode):
        if currentNode is None:
            return 0
        else:
            return max(self.getHeightRecursive(currentNode.left), self.getHeightRecursive(currentNode.right)) + 1


    def updateBalance(self, givenNode):
        return 0

