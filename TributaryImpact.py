import arcpy
import os
from Intersection import Intersection
from AVLPointsTree import AVLPointsTree
from math import e, log

def main(streamNetwork,
         dem,
         flowAccumulation,
         clippingRegion,
         outputFolder,
         outputName):
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")

    """Creates the temporary data folder, where we'll put all our intermediate results"""
    if not os.path.exists(outputFolder+"\\temporaryData"):
        os.makedirs(outputFolder+"\\temporaryData")
    tempData = outputFolder + "\\temporaryData"

    """Clips our stream network to a clipping region, if necessary"""
    if clippingRegion:
        clippedStreamNetwork = tempData + "\\" + outputName + "StrmNtWrk.shp"
        arcpy.AddMessage("Clipping stream network...")
        arcpy.Clip_analysis(streamNetwork, clippingRegion, clippedStreamNetwork)
    else:
        clippedStreamNetwork = streamNetwork

    streamSR = arcpy.Describe(streamNetwork).spatialReference
    demSR = arcpy.Describe(dem).spatialReference
    if streamSR.PCSName != demSR.PCSName:
        arcpy.AddError("DEM AND STREAM NETWORK USE DIFFERENT PROJECTIONS")

    spatialReference = arcpy.Describe(streamNetwork).spatialReference

    """Calculates our flow accumulation, if necessary"""
    if flowAccumulation is None:
        arcpy.AddMessage("Calculating Flow Accumulation...")
        filledDEM = arcpy.sa.Fill(dem)
        flowDirection = arcpy.sa.FlowDirection(filledDEM)
        flowAccumulation = arcpy.sa.FlowAccumulation(flowDirection)  # Calculates the flow accumulation to use in findWidth()

    cellSizeX = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEX")
    cellSizeY = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEY")
    cellSize = float(cellSizeX.getOutput(0)) * float(cellSizeY.getOutput(0))

    numReaches = int(arcpy.GetCount_management(clippedStreamNetwork).getOutput(0))

    intersectionArray = findIntersections(clippedStreamNetwork, numReaches)

    arcpy.AddMessage("Intersections to calculate: " + str(len(intersectionArray)))

    calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData)

    createProject(dem, streamNetwork, clippingRegion, outputFolder, clippedStreamNetwork, outputName, spatialReference,
                  intersectionArray)


"""Goes through the stream network and finds the intersections in the stream network"""
def findIntersections(streamNetwork, numReaches):
    arcpy.AddMessage("Finding intersections...")

    intersections = []
    points = AVLPointsTree()
    reqReachLength = 50

    polylineCursor = arcpy.da.SearchCursor(streamNetwork, ["SHAPE@"])

    row = polylineCursor.next()
    currentStream = row[0]
    if currentStream.length > reqReachLength:
        points.addNode(currentStream.lastPoint, currentStream)

    previousStream = currentStream

    for i in range(numReaches - 1):
        """If the current stream has a point that """
        row = polylineCursor.next()
        currentStream = row[0]
        pointInTree = points.findPoint(currentStream.lastPoint)
        continuousStreams = pointsAreEqual(previousStream.lastPoint, currentStream.firstPoint, .01)
        if pointInTree is not None:
            if currentStream.length < reqReachLength and continuousStreams: # If the stream is really short, we want to use the stream before it if possible, to get a better DA value
                intersections.append(Intersection(currentStream.lastPoint, currentStream, pointInTree.stream))
            else:
                intersections.append(Intersection(currentStream.lastPoint, currentStream, pointInTree.stream))
        else:
            if currentStream.length < reqReachLength and continuousStreams:
                points.addNode(currentStream.lastPoint, currentStream)
            else:
                points.addNode(currentStream.lastPoint, currentStream)

        previousStream = currentStream
    del row, polylineCursor
    arcpy.AddMessage("Intersections found")

    return intersections

"""Takes the streams and the point and uses them to calculate the impact of the tributary on the mainstem"""
def calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData):
    arcpy.AddMessage("Calculating Impact Probability...")
    i = 0

    arcpy.SetProgressor("step", "Calculating intersection " + str(i) + " out of " + str(len(intersectionArray)), 0,
                        len(intersectionArray), 1)
    for intersection in intersectionArray:
        i += 1
        try:
            streamOneDrainageArea = findFlowAccumulation(intersection.streamOne, flowAccumulation, cellSize, tempData)
            streamTwoDrainageArea = findFlowAccumulation(intersection.streamTwo, flowAccumulation, cellSize, tempData)
            if streamOneDrainageArea < 0 or streamTwoDrainageArea < 0:
                raise ValueError("Could not properly find drainage area")

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
            if tributarySlope == -9999:
                raise ValueError("Could not properly find slope")

            if mainstemDrainageArea < 1.0:
                varAr = 0
                mainstemDrainageArea = 0.0001
            else:
                varAr = tributaryDrainageArea / mainstemDrainageArea
            varPsiT = tributaryDrainageArea * tributarySlope

            varAr = abs(varAr)
            varPsiT = abs(varPsiT)
            if varAr == 0:
                varAr = 0.0001
            if varPsiT == 0:
                varPsiT = 0.0001

            eToPower = e**(8.68 + 6.08*log(varAr) + 10.04*log(varPsiT))
            impact = eToPower / (eToPower + 1)
            intersection.setImpact(impact)
            intersection.mainDrainArea = mainstemDrainageArea
            intersection.tribDrainArea = tributaryDrainageArea

            arcpy.SetProgressorLabel("Calculating intersection " + str(i) + " out of " + str(len(intersectionArray)))
            arcpy.SetProgressorPosition()

        except ValueError as error:
            arcpy.AddWarning(str(error))


"""Finds flow accumulation at a certain point"""
def findFlowAccumulation(stream, flowAccumulation, cellSize, tempData):
    """Because our stream network doesn't line up perfectly with our flow accumulation map, we need to create a
         buffer and search in that buffer for the max flow accumulation using Zonal Statistics"""
    arcpy.env.workspace = tempData
    arcpy.CreateFeatureclass_management(tempData, "point.shp", "POINT", "", "DISABLED", "DISABLED")
    cursor = arcpy.da.InsertCursor(tempData+"\point.shp", ["SHAPE@"])
    cursor.insertRow([stream.firstPoint]) # We use the first point so that we have a better chance of getting distinct values for DA
    del cursor

    try:
        arcpy.Buffer_analysis(tempData + "\point.shp", tempData + "\pointBuffer.shp", "20 Meters")
        arcpy.PolygonToRaster_conversion(tempData + "\pointBuffer.shp", "FID", tempData + "\pointBufferRaster.tif")
        maxFlow = arcpy.sa.ZonalStatistics(tempData + "\pointBufferRaster.tif", "Value", flowAccumulation, "MAXIMUM")
        arcpy.sa.ExtractValuesToPoints(tempData + "\point.shp", maxFlow, tempData + "\\flowPoint")
    except :
        return -9999


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


"""Gets the elevation at two points, then returns the slope between those two points"""
def findSlope(stream, dem, tempData):
    try:
        elevationOne = findElevationAtPoint(dem, stream.firstPoint, tempData)
        elevationTwo = findElevationAtPoint(dem, stream.lastPoint, tempData)
        return abs(elevationOne - elevationTwo) / stream.length
    except:
        return -9999


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

"""Writes output, and also writes the intersection data onto the clipped network"""
def writeOutput(intersectionArray, outputDataPath, outputName, spatialReference, streamNetwork):
    pointFolder = makeFolder(outputDataPath, "01_Points")
    arcpy.env.workspace = pointFolder

    outputShape = arcpy.CreateFeatureclass_management(pointFolder, outputName + "Points.shp", "POINT", "", "DISABLED", "DISABLED", spatialReference)
    arcpy.AddField_management(outputShape, "ImpactProb", "DOUBLE")

    insertCursor = arcpy.da.InsertCursor(outputShape, ["SHAPE@", "ImpactProb"])
    for intersection in intersectionArray:
        insertCursor.insertRow([intersection.point, intersection.impact])
    del insertCursor

    arcpy.AddField_management(streamNetwork, "UStreamIP", "DOUBLE")
    arcpy.AddField_management(streamNetwork, "DStreamIP", "DOUBLE")
    rows = arcpy.da.UpdateCursor(streamNetwork, ["SHAPE@", "DStreamIP", "UStreamIP"])
    arcpy.AddMessage("Adding output to clipped stream network...")

    numReaches = int(arcpy.GetCount_management(streamNetwork).getOutput(0))
    numReachesString = str(numReaches)

    i = 1
    arcpy.SetProgressor("step", "Adding to row " + str(i) + " out of " + numReachesString, 0,
                        numReaches, 1)
    for row in rows:
        currentStream = row[0]
        for intersection in intersectionArray:
            if pointsAreEqual(currentStream.firstPoint, intersection.point, .01):
                row[1] = intersection.impact
                rows.updateRow(row)
            if pointsAreEqual(currentStream.lastPoint, intersection.point, .01):
                row[2] = intersection.impact
                rows.updateRow(row)

        i += 1
        arcpy.SetProgressorLabel("Adding to row " + str(i) + " out of " + numReachesString)
        arcpy.SetProgressorPosition()

    del row
    del rows

    streamFolder = makeFolder(outputDataPath, "02_StreamNetwork")
    arcpy.Copy_management(streamNetwork, streamFolder + "/TribImpactStrmNtwrk.shp")


def createProject(dem, streamNetwork, clippingRegion, outputFolder, clippedStreamNetwork, outputName, spatialReference,
                  intersectionArray):
    """
    Copies everything over into a folder and writes the XML file for it
    :param dem: The path to the DEM
    :param streamNetwork: The path to the original stream network
    :param clippingRegion: The path to the clipping region, if applicable
    :param outputFolder: Where we want to put the project
    :param clippedStreamNetwork: The result of the clipping
    :param outputName: What we want to name our output
    :param spatialReference: The spatial reference of the stream network
    :param intersectionArray: The array of intersections that we have
    :return: None
    """
    projectFolder = makeFolder(outputFolder, "TribImpactProject")

    inputsFolder = makeFolder(projectFolder, "01_Inputs")
    analysesFolder = makeFolder(projectFolder, "02_Analyses")

    demFolder = makeFolder(inputsFolder, "01_DEM")
    arcpy.Copy_management(dem, os.path.join(demFolder, os.path.join(os.path.basename(dem))))
    streamNetworkFolder = makeFolder(inputsFolder, "02_StreamNetwork")
    arcpy.Copy_management(streamNetwork, os.path.join(streamNetworkFolder, os.path.basename(streamNetwork)))
    if clippingRegion:
        clippingRegionFolder = makeFolder(inputsFolder, "03_ClippingRegionFolder")
        arcpy.Copy_management(clippingRegion, os.path.join(clippingRegionFolder, os.path.basename(clippingRegion)))

    outputFolder = getOutputFolder(analysesFolder)

    writeOutput(intersectionArray, outputFolder, outputName, spatialReference, clippedStreamNetwork)


def getOutputFolder(analysesFolder):
    """
    Gets us the first untaken Output folder number, makes it, and returns it
    :param analysesFolder: Where we're looking for output folders
    :return: String
    """
    i = 1
    outputFolder = os.path.join(analysesFolder, "Output_" + str(i))
    while os.path.exists(outputFolder):
        i += 1
        outputFolder = os.path.join(analysesFolder, "Output_" + str(i))

    os.mkdir(outputFolder)
    return outputFolder


def makeFolder(pathToLocation, newFolderName):
    """
    Makes a folder and returns the path to it
    :param pathToLocation: Where we want to put the folder
    :param newFolderName: What the folder will be called
    :return: String
    """
    newFolder = os.path.join(pathToLocation, newFolderName)
    if not os.path.exists(newFolder):
        os.mkdir(newFolder)
    return newFolder


def pointsAreEqual(pointOne, pointTwo, buf):
    x1 = float(pointOne.X)
    x2 = float(pointTwo.X)
    y1 = float(pointOne.Y)
    y2 = float(pointTwo.Y)
    return (x1 - buf) < x2 < (x1 + buf) and (y1 - buf) < y2 < (y1 + buf)

