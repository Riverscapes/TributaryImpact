import arcpy, os
from Intersection import Intersection
from AVLPointsTree import AVLPointsTree
from math import sqrt, e, log

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

    numReaches = int(arcpy.GetCount_management(clippedStreamNetwork).getOutput(0))

    intersectionArray = findIntersections(clippedStreamNetwork, numReaches)

    calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, numReaches, tempData)

    writeOutput(intersectionArray, outputDataPath, outputName, spatialReference)


def findIntersections(streamNetwork, numReaches):
    arcpy.AddMessage("Finding intersections...")
    numReachesString = str(numReaches)
    arcpy.AddMessage("Reaches in network: " + numReachesString)

    intersections = []
    points = AVLPointsTree()
    reqReachLength = 50

    polylineCursor = arcpy.da.SearchCursor(streamNetwork, ["SHAPE@"])
    j = 0
    previousStream = None
    for i in range(numReaches):
        """If the current stream has a point that """
        arcpy.AddMessage("Finding intersections...")
        row = polylineCursor.next()
        currentStream = row[0]
        pointInTree = points.findPoint(currentStream.lastPoint)
        if pointInTree is not None:
            if currentStream.length < reqReachLength and previousStream.lastPoint.equals(currentStream.firstPoint):
                intersections.append(Intersection(currentStream.lastPoint, previousStream, pointInTree.stream))
            else:
                intersections.append(Intersection(currentStream.lastPoint, currentStream, pointInTree.stream))
        else:
            if currentStream.length < reqReachLength and previousStream.lastPoint.equals(currentStream.firstPoint):
                points.addNode(currentStream.lastPoint, previousStream)
            else:
                points.addNode(currentStream.lastPoint, currentStream)

        previousStream = currentStream
    del row, polylineCursor

    arcpy.AddMessage(str(points.getSize()))
    return intersections


def calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, numReaches, tempData):
    arcpy.AddMessage("Calculating Impact Probability...")
    i = 0
    for intersection in intersectionArray:
        i += 1
        arcpy.AddMessage("Calculating intersection " + str(i) + " out of " + str(len(intersectionArray)) +
                         " (" + str(float(i) / float(len(intersectionArray)) * 100) + "% done)")
        streamOneDrainageArea = findFlowAccumulation(intersection.streamOne, flowAccumulation, cellSize, tempData)
        streamTwoDrainageArea = findFlowAccumulation(intersection.streamTwo, flowAccumulation, cellSize, tempData)

        if streamOneDrainageArea > streamTwoDrainageArea:
            mainstem = intersection.streamOne
            mainstemDrainageArea = streamOneDrainageArea
            tributary = intersection.streamTwo
            tributaryDrainageArea = streamTwoDrainageArea
        else:
            tributary = intersection.streamOne
            tributaryDrainageArea = streamOneDrainageArea
            mainstem = intersection.streamTwo
            mainstemDrainageArea = streamTwoDrainageArea

        tributarySlope = findSlope(tributary, dem, tempData)

        varAr = tributaryDrainageArea / mainstemDrainageArea
        varPsiT = tributaryDrainageArea * tributarySlope

        varAr = abs(varAr)
        varPsiT = abs(varPsiT)
        if varAr == 0:
            varAr = 0.0001
        if varPsiT == 0:
            varPsiT = 0.0001

        eToPower = e**(8.68 + 6.08*log(varAr) + 10.04*log(varPsiT))
        intersection.setImpact(eToPower / (eToPower + 1))

    i = 0


def findFlowAccumulation(stream, flowAccumulation, cellSize, tempData):
    """Because our stream network doesn't line up perfectly with our flow accumulation map, we need to create a
         buffer and search in that buffer for the max flow accumulation using Zonal Statistics"""
    #sr = arcpy.Describe(stream).spatialReference
    arcpy.env.workspace = tempData
    arcpy.CreateFeatureclass_management(tempData, "point.shp", "POINT", "", "DISABLED", "DISABLED")
    cursor = arcpy.da.InsertCursor(tempData+"\point.shp", ["SHAPE@"])
    cursor.insertRow([stream.firstPoint])
    del cursor
    arcpy.Buffer_analysis(tempData + "\point.shp", tempData + "\pointBuffer.shp", "20 Meters")
    arcpy.PolygonToRaster_conversion(tempData + "\pointBuffer.shp", "FID", tempData + "\pointBufferRaster.tif")
    maxFlow = arcpy.sa.ZonalStatistics(tempData + "\pointBufferRaster.tif", "Value", flowAccumulation, "MAXIMUM")
    arcpy.sa.ExtractValuesToPoints(tempData + "\point.shp", maxFlow, tempData + "\\flowPoint")

    searchCursor = arcpy.da.SearchCursor(tempData + "\\flowPoint.shp", "RASTERVALU")
    row = searchCursor.next()
    flowAccAtPoint = row[0]
    del row
    del searchCursor
    flowAccAtPoint *= cellSize  # gives us the total area of flow accumulation, rather than just the number of cells
    flowAccAtPoint /= 1000000  # converts from square meters to square kilometers
    if flowAccAtPoint < 0:
        flowAccAtPoint = 0

    return flowAccAtPoint


def findSlope(stream, dem, tempData):
    elevationOne = findElevationAtPoint(dem, stream.firstPoint, tempData)
    elevationTwo = findElevationAtPoint(dem, stream.lastPoint, tempData)
    return abs(elevationOne - elevationTwo) / stream.length


def findElevationAtPoint(dem, point, tempData):
    """Finds the elevation at a certain point based on a DEM"""
    """
    I can't find a good way to just pull the data straight from the raster, so instead, we're having to
    create the point in a layer of its own, then create another layer that has the elevation using the Extract Value
    to Points tool, then using a search cursor to get the elevation data. It's a mess, and it's inefficient, but it
    works. If anyone can find a better way, email me at banderson1618@gmail.com
    """
    sr = arcpy.Describe(dem).spatialReference
    arcpy.env.workspace = tempData
    arcpy.CreateFeatureclass_management(tempData, "point.shp", "POINT", "", "DISABLED", "DISABLED", sr)
    cursor = arcpy.da.InsertCursor(tempData + "\point.shp", ["SHAPE@"])
    cursor.insertRow([point])
    del cursor
    pointLayer = tempData + "\pointElevation"
    arcpy.sa.ExtractValuesToPoints(tempData + "\point.shp", dem, pointLayer)
    searchCursor = arcpy.da.SearchCursor(pointLayer + ".shp", "RASTERVALU")
    row = searchCursor.next()
    elevation = row[0]
    del searchCursor
    del row

    return elevation


def writeOutput(intersectionArray, outputDataPath, outputName, spatialReference):
    arcpy.env.workspace = outputDataPath

    outputShape = arcpy.CreateFeatureclass_management(outputDataPath, outputName+ ".shp", "POINT", "", "DISABLED", "DISABLED", spatialReference)
    arcpy.AddField_management(outputShape, "ImpactProb", "DOUBLE")

    insertCursor = arcpy.da.InsertCursor(outputShape, ["SHAPE@", "ImpactProb"])
    for intersection in intersectionArray:
        insertCursor.insertRow([intersection.point, intersection.impact])
    del insertCursor


    tempLayer = outputDataPath + "\\" +  outputName+ "_lyr"
    outputLayer = outputDataPath + "\\" +  outputName+ ".lyr"
    arcpy.MakeFeatureLayer_management(outputShape, tempLayer)
    arcpy.SaveToLayerFile_management(tempLayer, outputLayer)






















