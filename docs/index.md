---
title: Tributary Impact Tool
---

# About
The Tributary Impact Tool is a Python script for ArcGIS which finds intersections in a stream network and calculates the percent chance of the tributary creating a large fan in the mainstem when the tributary dumps its sediment load. The equation used to find this percentage is based on the one found in the paper *Tributary Connectivity, Confluence Aggradation and Network Biodiversity* by Stephen P. Rice. A full citation for the paper can be found at the bottom of the page.

# Inputs
The tool requires a stream network shape file, a DEM, a folder to place the output in, and a name to give to the output. The user can optionally provide the tool with a Flow Accumulation input to save time; if the user does not, the tool will create a temporary one for use in the tool automatically. The user can also provide the tool with a shapefile containing a polygon that the stream network will be clipped to. This can be useful if the user only wants to run the tool on a limited portion of the stream network.

# Running the Tool
<div align="center">
  <a class="button" href="https://github.com/Riverscapes/TributaryImpact/releases/latest"><i class="fa fa-github"/> Download Latest Release of Tributary Impact Tool</a>
  <a class="button" https://github.com/Riverscapes/TributaryImpact"><i class="fa fa-github"/> Visit Tributary Impact Tool Repo</a>  
</div>
  
#### Make sure all your inputs use the same projection
If the inputs use different projections, the tool will give you an error.
#### Keep the stream network over the DEM and Flow Accumulation map
The program won't crash if there is one stream that slips off the DEM, but the program will waste time trying to find the impact chance of data that isn't there. If large sections of your stream network are off of your DEM or Flow Accumulation map, use a clipping region to make sure the tool focuses on streams that it can find a result for.

# Outputs
The tool produces two outputs: a shapefile of points, and a shapefile with the stream network.

## Points
Each point has the percent chance of a large fan being created. These points coincide with the intersections in the stream network.

## Stream network
If the user doesn't use a clipping region, the stream network is a copy of the entire network. If the user does use a clipping region, the stream network is the entire network, clipped to the clipping region. The stream network is given two new attributes: an upstream impact chance, labeled as "UStreamIP", and a downstream impact chance, labeled as "DStreamIP". The upstream impact chance indicates the chances of the stream being upstream of a large fan. The downstream impact chance indicates the chances of the stream being downstream of a large fan. These values are the same as the ones in the Points file, just displayed differently.

# Citation
- Rice SP. 2017. Tributary connectivity, confluence aggradation and network biodiversity. Geomorphology 277 : 6–16. DOI: [10.1016/j.geomorph.2016.03.027](http://dx.doi.org/10.1016/j.geomorph.2016.03.027)
