class PointNode:
    def __init__(self, value, stream=None):
        self.value = value
        self.stream = stream
        self.left = None
        self.right = None

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


class AVLPointsTree:
    def __init__(self):
        self.root = None

    def addNode(self, givenPoint, givenStream):
        newNode = PointNode(givenPoint, givenStream)
        if self.root is None:
            self.root = newNode
        else:
            if self.root < newNode:
                self.addNodeRecursive(newNode, self.root.right)
            else:
                self.addNodeRecursive(newNode, self.root.left)

    def addNodeRecursive(self, givenNode, currentNode):
        if currentNode is None:
            currentNode = givenNode
        elif currentNode < givenNode:
            self.addNodeRecursive(givenNode, currentNode.right)
        else:
            self.addNodeRecursive(givenNode, currentNode.left)

    def findPoint(self, givenValue):
        newNode = PointNode(givenValue)
        return self.findPointRecursive(newNode, self.root)

    def findPointRecursive(self, givenNode, currentNode):
        if currentNode is None:
            return None
        elif currentNode == givenNode:
            return currentNode
        elif currentNode > givenNode:
            return self.treeContains(givenNode, currentNode.left)
        else:
            return self.treeContains(givenNode, currentNode.right)