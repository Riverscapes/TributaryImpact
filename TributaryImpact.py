import arcpy, os
from Intersection import Intersection
from AVLPointsTree import AVLPointsTree

def main(streamNetwork,
         dem,
         clippingRegion,
         outputFolder,
         outputName,
         testing):
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    """Creates the temporary data folder, where we'll put all our intermediate results"""
    if not os.path.exists(outputFolder+"\\temporaryData"):
        os.makedirs(outputFolder+"\\temporaryData")
    tempData = outputFolder + "\\temporaryData"

    """Creates our output folder, where we'll put our final results"""
    if not os.path.exists(outputFolder+"\TributaryImpactPoints"):
        os.makedirs(outputFolder+"\TributaryImpactPoints")
    outputDataPath = outputFolder+"\TributaryImpactPoints"

    """Clips our stream network to a clipping region, if necessary"""
    if clippingRegion is not None:
        clippedStreamNetwork = tempData + "\clippedStreamNetwork.shp"
        arcpy.AddMessage("Clipping stream network...")
        arcpy.Clip_analysis(streamNetwork, clippingRegion, clippedStreamNetwork)
    else:
        clippedStreamNetwork = streamNetwork

    spatialReference = arcpy.Describe(streamNetwork).spatialReference

    arcpy.AddMessage("Calculating Flow Accumulation...")
    filledDEM = arcpy.sa.Fill(dem)
    flowDirection = arcpy.sa.FlowDirection(filledDEM)
    flowAccumulation = arcpy.sa.FlowAccumulation(flowDirection)  # Calculates the flow accumulation to use in findWidth()
    cellSizeX = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEX")
    cellSizeY = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEY")
    cellSize = float(cellSizeX.getOutput(0)) * float(cellSizeY.getOutput(0))

    intersectionArray = findIntersections(clippedStreamNetwork, tempData)

    calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData)

    writeOutput(intersectionArray, outputDataPath, outputName, spatialReference)


def findIntersections(streamNetwork, tempData):
    arcpy.AddMessage("Finding intersections...")
    numReaches = int(arcpy.GetCount_management(streamNetwork).getOutput(0))
    numReachesString = str(numReaches)
    arcpy.AddMessage("Reaches in network: " + numReachesString)

    intersections = []
    points = AVLPointsTree()

    polylineCursor = arcpy.da.SearchCursor(streamNetwork, ["SHAPE@"])
    row = polylineCursor.next()
    previousStream = row[0]
    for i in range(numReaches - 1):
        """If the current stream has a point that """
        arcpy.AddMessage("Evaluating Reach: " + str(i))
        row = polylineCursor.next()
        currentStream = row[0]
        arcpy.AddMessage("Point: " + str(previousStream.lastPoint.X) + " " + str(previousStream.lastPoint.Y))
        pointInTree = points.findPoint(previousStream.lastPoint)
        if pointInTree is not None:
            intersections.append(Intersection(previousStream.lastPoint, previousStream, pointInTree.stream))
        else:
            arcpy.AddMessage("Size: " + str(points.getSize()))
            arcpy.AddMessage("Height: " + str(points.getHeight()))
            points.addNode(previousStream.lastPoint, previousStream)

        """
        if not currentStream.firstPoint.equals(previousStream.firstPoint) and not currentStream.firstPoint.equals(previousStream.lastPoint):
            if not currentStream.lastPoint.equals(previousStream.firstPoint) and not currentStream.lastPoint.equals(previousStream.lastPoint):
                arcpy.AddMessage("Point: " + str(previousStream.lastPoint.X) + " " + str(previousStream.lastPoint.Y))
                pointInTree = points.findPoint(previousStream.lastPoint)
                if pointInTree is not None:
                    intersections.append(Intersection(previousStream.lastPoint, previousStream, pointInTree.stream))
                else:
                    arcpy.AddMessage("Size: " + str(points.getSize()))
                    arcpy.AddMessage("Height: " + str(points.getHeight()))
                    points.addNode(previousStream.lastPoint, previousStream)                  
        """
        previousStream = currentStream

    arcpy.AddMessage(str(points.getSize()))
    return intersections


def calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData):
    #TODO: Write calculateImpact()
    i = 0


def writeOutput(intersectionArray, outputDataPath, outputName, spatialReference):
    arcpy.env.workspace = outputDataPath

    outputShape = arcpy.CreateFeatureclass_management(outputDataPath, outputName+ ".shp", "POINT", "", "DISABLED", "DISABLED", spatialReference)

    insertCursor = arcpy.da.InsertCursor(outputShape, ["SHAPE@"])
    for intersection in intersectionArray:
        insertCursor.insertRow([intersection.point])
    del insertCursor

    tempLayer = outputDataPath + "\\" +  outputName+ "_lyr"
    outputLayer = outputDataPath + "\\" +  outputName+ ".lyr"
    arcpy.MakeFeatureLayer_management(outputShape, tempLayer)
    arcpy.SaveToLayerFile_management(tempLayer, outputLayer)






















