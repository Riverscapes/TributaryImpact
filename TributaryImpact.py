import arcpy, os
from Intersection import Intersection

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

    arcpy.AddMessage("Calculating Flow Accumulation...")
    filledDEM = arcpy.sa.Fill(dem)
    flowDirection = arcpy.sa.FlowDirection(filledDEM)
    flowAccumulation = arcpy.sa.FlowAccumulation(flowDirection)  # Calculates the flow accumulation to use in findWidth()
    cellSizeX = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEX")
    cellSizeY = arcpy.GetRasterProperties_management(flowAccumulation, "CELLSIZEY")
    cellSize = float(cellSizeX.getOutput(0)) * float(cellSizeY.getOutput(0))

    intersectionArray = findIntersections(clippedStreamNetwork, tempData)

    calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData)

    writeOutput(intersectionArray, outputDataPath)


def findIntersections(streamNetwork, tempData):
    #TODO: Write findIntersections()
    arcpy.AddMessage("Finding intersections...")
    numReaches = int(arcpy.GetCount_management(streamNetwork).getOutput(0))
    numReachesString = str(numReaches)
    arcpy.AddMessage("Reaches in network: " + numReachesString)
    intersections = []
    points = []
    polylineCursor = arcpy.da.SearchCursor(streamNetwork, ["SHAPE@"])
    for i in range(numReaches):
        


    return intersections


def calculateImpact(intersectionArray, dem, flowAccumulation, cellSize, tempData):
    #TODO: Write calculateImpact()
    i = 0


def writeOutput(intesectionArray, outputDataPath):
    i = 0






















