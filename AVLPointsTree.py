class PointNode:
    def __init__(self, value, stream=None):
        self.value = value
        self.stream = stream
        self.left = None
        self.right = None
        self.parent = None

    def isRoot(self):
        return self.parent == None

    def isLeftChild(self):
        if self.parent == None:
            return False
        else:
            return self.parent.left == self

    def isRightChild(self):
        if self.parent == None:
            return False
        else:
            return self.parent.right == self

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
                self.updateBalance(givenNode)
        else:
            if currentNode.left is not None:
                self.addNodeRecursive(givenNode, currentNode.left)
            else:
                currentNode.left = givenNode
                givenNode.parent = currentNode
                self.updateBalance(givenNode)


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
        rightHeight = self.getHeightRecursive(givenNode.right)
        leftHeight = self.getHeightRecursive(givenNode.left)
        if abs(rightHeight - leftHeight) > 1:
            self.rebalance(givenNode, rightHeight, leftHeight)
        if givenNode.parent != None:
            self.updateBalance(givenNode.parent)


    def rebalance(self, givenNode, rightHeight, leftHeight):
        if rightHeight > leftHeight:
            if self.getHeightRecursive(givenNode.right.left) > self.getHeightRecursive(givenNode.right.right):
                self.rotateRight(givenNode.right)
                self.rotateLeft(givenNode)
            else:
                self.rotateLeft(givenNode)
        else:
            if self.getHeightRecursive(givenNode.left.right) > self.getHeightRecursive(givenNode.left.left):
                self.rotateLeft(givenNode.left)
                self.rotateRight(givenNode)
            else:
                self.rotateRight(givenNode)


    def rotateRight(self, rotateRoot):
        newRoot = rotateRoot.left
        parent = rotateRoot.parent
        if parent == None:
            self.root = newRoot
        elif parent.left == rotateRoot:
            parent.left = newRoot
        else:
            parent.right = newRoot

        rotateRoot.left = newRoot.right
        if rotateRoot.left != None:
            rotateRoot.left.parent = rotateRoot
        newRoot.right = rotateRoot
        rotateRoot.parent = newRoot
        newRoot.parent = parent


    def rotateLeft(self, rotateRoot):
        newRoot = rotateRoot.right
        parent = rotateRoot.parent
        if parent == None:
            self.root = newRoot
        elif parent.left == rotateRoot:
            parent.left = newRoot
        else:
            parent.right = newRoot

        rotateRoot.right = newRoot.left
        if rotateRoot.right != None:
            rotateRoot.right.parent = rotateRoot
        newRoot.left = rotateRoot
        rotateRoot.parent = newRoot
        newRoot.parent = parent

