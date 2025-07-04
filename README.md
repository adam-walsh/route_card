# Introduction

This programme takes a gpx file and creates a route card from it. 

A route card is a piece of paper you prepare ehile planning a hike or walk to help with navigation, communicate to other people where you are going and give you a sense of how long each leg of the route should take. The route card created by this programme will have some information about the distance between points and total distances but not any information about the timing. Timing information is one of the most importat parts of a route card. You should fill in your own timing information based off distance, elevation, terrain and the group completing the hike.

This programme will only work in Ireland but could be adjusted by changing the coordinte system. Note that if used outside of ireland the use of the irish co-ordinate system will break distance measurements as well as give useless results for co-ordinates.
It decides which points to show on the route card by looking for a card point flag. The card point flag is "cp" by defalut but can be changed by the user. The card point must appear in either the description, comment or name of a point, for it to appear in the route card. 

I decided to write this programme because I noticed I rairly took the time to make a route card when hiking, even though they contain a lot of useful information. The hope is that this programme will make it faster to create a route card and therefore make me more likely to use one.

The programme is written in python and is intended to be run either from the command line or imported as a module for other programmes.

# Getting started
## prerequisits

This project is written entirely in python so should work on linux, windows or mac. It was writeen in Python 3.12.3. I haven't checked but it probably works with similar python versions.

## requirements

I have not checked what versions work for this, only listed the versions I know do. The required python modules for this package are listed in the reequirements.txt file of this repo as well as below:

- et_xmlfile==2.0.0
- gpxpy==1.6.2
- numpy==2.2.5
- openpyxl==3.1.5
- pandas==2.3.0
- pygeomag==1.1.0
- pyproj==3.7.1
- python-dateutil==2.9.0.post0
- pytz==2025.2
- six==1.17.0
- style==1.1.0
- tzdata==2025.2

If using a virtual environment on a linux based operating system then all packages can be installed using the below command:

    python -m pip install requirements.txt -r

# Usage

## Basic Usage

### Preparing the GPX file

GPX files can be creating by exporting routes/plans from most mapping applications. When creating your route you must decide which points whould end up in the route card. These should be points that are simple to re-locate yourself at and figure out where you are using close features. To flag points as "card points" that should show up on the route card they must have the card point flag. By default the card point flag is "cp" (case sensitive). The card point flag can be added to a points name, description or comment. The card point flag can be set to a different string using the "--flag" option when calling the programme.

When placing points along the route it is important to ensure all elevatoin change is captured. Note that this is not talking about placing route card points but the actual points that make up the route before it is exported to gpx. If you are using any kind of a follow paths feature on a mapping application then it will place plenty of points along the route it creates along a path. If you are not using a follow path feature and placing points for a straight line route then there are extra considerations. If there is elevation gain followed by elevatoin loss between points then only the net elevation change will be captured by this programme. For example if the route went up 50 m and down 30 m between 2 points, this programme would count that as only going up 20 m and not going down at all. The solution in that situation is to put a point at the top.

It is best practice not to include any spaces or special characters in the filename of your gpx file. This will make your file easier to work with and pass to the programme.

### Running the programme from the terminal

To run the programme navigate to the project directory and run the following command:

    python main.py your_route.gpx -o output_filename.csv

Where "your_route.gpx" is the name of your gpx file nad "output_fliname" is the name of the file you want the output to be written to.


For information on running the programme you can access a help message by navigating to the project directory and running the following command:

    python main.py --help

### Interpreting the output from the programme

A sample output file can be viewed in the route_card.csv and route_card.xlsx files. Note that the Distance, Ascent and Descent 

(should put a screenshot of sample file here)

## Adjusting Elevation Change Parameters

## Calling Functions from Other Programmes

# Methodology and Background

# Notes

I still need to finish the README file :/