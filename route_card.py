"""
filename:       route_card.py
Author:         Adam Walsh
Date:           02/07/2025
Description:    This function takes a gpx file and creates a route card from it. It decides which points to include in the
                route card by checking for a flag somewhere in the point. It should work with either gpx routes and tracks.
"""

import gpxpy
import pyproj
import argparse
import numpy as np
import pandas as pd
from datetime import datetime as dt
from pygeomag import GeoMag

# constants whose values whould not be changed after this block
# ==============================================================================================================================
DEFAULT_GRID_FIGS = 6   # by default a 6 figure grid reference is used
DEFAULT_ELE_BAND_WIDTH = 5 # resolution of elevation for calculating change in elevation in meters
AUTO_ELE_BUFFER = -1   # tells the function to set the elevation buffer itself. Used with band width for changes in elevation
DEFAULT_CARD_POINT_FLAG = "cp" # the string that tells the programme to include a point in the route card
DEFAULT_OUTPUT_FILE = r"route_card.csv"
# ==============================================================================================================================

# Every point along the route is stored as a route point not just the points that appear on the route card.
# Elevation change is calculated as a net change between route points so if there is ascent followed by 
# descent between points, that is lost. This is more relevant when placing points manually instead of an app 
# placing them along a path because apps place a lot of points. 
class route_point:
    def __init__(self, gpx_point, transformer, ele_band_prev, card_point_flag, ele_band_width, ele_buffer) :
        self.lat, self.lon, self.elevation = gpx_point.latitude, gpx_point.longitude, gpx_point.elevation
        self.card_point_flag = check_if_card_point(gpx_point, card_point_flag) 
        self.easting, self.northing = transformer.transform(gpx_point.latitude, gpx_point.longitude) 
        self.dist_from_prev  = self.ascent_from_prev = self.descent_from_prev = 0
        self.elevation_band = discretize_elevation(self.elevation, ele_band_prev, ele_band_width, ele_buffer)
 
    def join_to(self, prev_point):  # calculate values based off trip from from the previous point
        # assume flat earth
        self.dist_from_prev = np.sqrt((self.easting-prev_point.easting)**2 + (self.northing-prev_point.northing)**2) 
        elevation_change = self.elevation_band - prev_point.elevation_band
        if elevation_change > 0:
            self.ascent_from_prev = elevation_change
        else:
            self.descent_from_prev = elevation_change

# this class stores information about only the points that will appear on the route card, not every point along the route
class card_point:
    def __init__(self, point, points_since_prev_card_point, prev_card_point, magnetic_variation, earth_model, figs_grid_ref):
        self.grid_ref = irish_grid_ref2map_ref(point.easting, point.northing, figs_grid_ref)
        self.dist_from_prev = self.ascent_from_prev = self.descent_from_prev = 0
        self.lat, self.lon = point.lat, point.lon
        
        if magnetic_variation == "first_point":
            self.compass_bearing = self.dist_from_prev = self.ascent_from_prev = self.descent_from_prev = 0
            self.dist_accumulative = self.ascent_accumulative = self.descent_accumulative = 0
            return
        
        for point in points_since_prev_card_point[1::]:
            self.dist_from_prev += point.dist_from_prev 
            self.ascent_from_prev += point.ascent_from_prev 
            self.descent_from_prev += point.descent_from_prev 
        
        self.dist_accumulative = prev_card_point.dist_accumulative + self.dist_from_prev
        self.ascent_accumulative = prev_card_point.ascent_accumulative + self.ascent_from_prev
        self.descent_accumulative = prev_card_point.descent_accumulative + self.descent_from_prev

        grid_bearing = earth_model.inv(prev_card_point.lon, prev_card_point.lat, point.lon, point.lat)[0]
        self.compass_bearing = (grid_bearing + magnetic_variation)%360
    

def irish_grid_ref2map_ref(easting, northing, figs_grid_ref):
    irish_grid_letter_layout = [['a', 'b', 'c', 'd', 'e'],  # there is no I because it looks like a 1
                                ['f', 'g', 'h', 'j', 'k'],
                                ['l', 'm', 'n', 'o', 'p'],
                                ['q', 'r', 's', 't', 'u'],
                                ['v', 'w', 'x', 'y', 'z']]
    letter_box_width = letter_box_height = 100000
    trimmed_digits = (10-figs_grid_ref)/2
    x = str(int(easting % letter_box_width // 10**trimmed_digits)).zfill(figs_grid_ref//2)
    y = str(int(northing % letter_box_height // 10**trimmed_digits)).zfill(figs_grid_ref//2)
    letter_index_x = int(easting // letter_box_width)
    letter_index_y = int(northing // letter_box_height)
    letter = irish_grid_letter_layout[letter_index_y][letter_index_x]
    return f"{letter} {x} {y}"

# the elevation is discretized to bring the elevation difference in line with how a person would calculate it
# if the obvious method of adding up all of the diferences in elevation is used then the elevation is much higher
# hiiker, garmin explore and outdoor active can all give different elevation differences for the same gpx file
# the ELEVATION_BAND_WIDTH and ELEVATION_HYSTERESIS constants can be adjusted to make consistent with different sources
def discretize_elevation(elevation, prev_elevation_band, ele_band_width, ele_buffer):
        if elevation > prev_elevation_band + ele_band_width + ele_buffer:  # if higher up
            return (elevation - ele_buffer) // ele_band_width * ele_band_width
        elif elevation < prev_elevation_band - ele_band_width - ele_buffer: # if lower down
            return (elevation + ele_buffer) // ele_band_width * ele_band_width
        else:   # if similar elevation
            return prev_elevation_band

def check_if_card_point(gpx_point, card_point_flag):
    possible_marker_locations = [gpx_point.name, gpx_point.comment, gpx_point.description]
    for possible_location in possible_marker_locations:
        if not (isinstance(possible_location, str)): # skip past empty fields
            continue
        if card_point_flag in possible_location:
            return 1
    return 0

def check_for_track(num_tracks, num_routes):
    if num_tracks > 1:
        raise Exception("Error: more than one track was found in the gpx file")
    if num_routes > 1:
        raise Exception("Error: more than one route was found in the gpx file")
    if num_tracks == 0 and num_routes == 0:
        raise Exception("Error: no route or track was found in the gpx file")
    if num_tracks == 1 and num_routes == 1:
        print("One track and one route were found in the gpx file. The track will be used for the route card")
        return 1
    if num_tracks == 1:
        return 1
    else:
        return 0

def extract_path(gpx):
    num_tracks = len(gpx.tracks)
    num_routes = len(gpx.routes)
    if check_for_track:
        points = np.concatenate([segment.points for segment in gpx.tracks[0].segments])
    else:
        points = np.concatenate(gpx.routes[0].points)
    return points

# returns magnetic variation in degrees at time of running the function
# magnetic variation is given from true north not from grid north
def mag_var_at_start(lat, lon, ele):
    dt_time = dt.today()
    gm_time = dt_time.year + dt_time.month*1/12
    geo_mag = GeoMag(coefficients_file="wmm/WMM_2025.COF")
    mag_var = geo_mag.calculate(glat=lat, glon=lon, alt=ele, time=gm_time).d
    return mag_var

# takes the full route and forms an array of points to be put on the route card
def full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref):
    model = pyproj.Geod(ellps='clrk66')
    card_points = [card_point(full_route[0], 0, 0, "first_point", 0, figs_grid_ref)]
    card_point_index = 0
    for i in range(1, num_gpx_points):
        if not (full_route[i].card_point_flag or i==num_gpx_points-1):
            continue
        prev_card_point_i = card_point_index
        card_point_i = i
        prec_card_point = card_points[-1:][0]
        cp = card_point(full_route[i], full_route[prev_card_point_i:i+1], card_points[-1:][0], mag_var, model, figs_grid_ref)
        card_points.append(cp)
    return card_points
    
def array2df(card_points):
    df = pd.DataFrame.from_records(vars(point) for point in card_points)
    df = df.drop(columns=["lat", "lon"])
    df = df.round(decimals=0)
    new_column_names = {"grid_ref":"Grid Reference",
                        "dist_from_prev":"Distance [m]",
                        "ascent_from_prev":"Ascent[m]",
                        "descent_from_prev":"Descent[m]",
                        "elevation":"Elevation [m]",
                        "compass_bearing":"Compass Bearing",
                        "ascent_accumulative":"Total Ascent [m]",
                        "descent_accumulative":"Total Descent [m]",
                        "dist_accumulative":"Total Distance [m]"}

    df = df.rename(columns=new_column_names)
    return df

def write_df_to_output(df, output_filename):
    file_extension = output_filename.split('.')[::-1][0]
    if file_extension == "xlsx": 
        df.to_excel(output_filename)
    elif file_extension == "csv":
        df.to_csv(output_filename)
    else:
        raise('Error: file extension "' + str(file_extension) +'" not supported.')
    print("Wrote output to "+output_filename)

def create_route_card(input_filename, output_filename, figs_grid_ref=DEFAULT_GRID_FIGS, card_point_flag=DEFAULT_CARD_POINT_FLAG,\
                      ele_band_width=DEFAULT_ELE_BAND_WIDTH, ele_buffer=AUTO_ELE_BUFFER):

    if ele_buffer==AUTO_ELE_BUFFER:
        ele_buffer = ele_band_width/5

    # read route into array of point objects from the gpxpy module 
    gpx_file = open(input_filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    gpx_file.close()
    gpx_points = extract_path(gpx)
    num_gpx_points = len(gpx_points)

    # convert to irish grid coordinates, calculate parameters and store as route_point objects
    mag_var = mag_var_at_start(gpx_points[0].latitude, gpx_points[0].longitude, gpx_points[0].elevation)
    global_coords = pyproj.Proj("epsg:4326")
    irish_grid = pyproj.Proj("epsg:29902")
    global_coords_to_irish_grid = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:29902")
    starting_elevation_band = gpx_points[0].elevation // ele_band_width * ele_band_width 
    full_route = np.empty(num_gpx_points, dtype=route_point) 
    full_route[0] = route_point(gpx_points[0], global_coords_to_irish_grid, starting_elevation_band,\
                                card_point_flag, ele_band_width, ele_buffer) 
    for i in range(1, num_gpx_points):
        full_route[i] = route_point(gpx_points[i], global_coords_to_irish_grid, full_route[i-1].elevation_band,\
        card_point_flag, ele_band_width, ele_buffer) 

    for i in range(1, num_gpx_points): 
        full_route[i].join_to(full_route[i-1])
    
    # create array of just points that should appear on the route card and calculate parameters
    card_points = full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref)
    df = array2df(card_points)

    write_df_to_output(df, output_filename)
           

parser = argparse.ArgumentParser(description= """
Creates a route card from a gpx file. The fields in the route card it makes are: 
Grid Reference, Distance, Ascent, Descent, Compass Bearing	Total Distance, Total Ascen, Total Descent.
Your route card should also have timing information but this programme doesn't do that for you. Do that yourself.
""")

help_msg = """The filename of the gpx file containing the route. Points must have the card point flag for the programme to
              add them to the route card."""
parser.add_argument("gpx_file", help=help_msg)
help_msg = """The filename for the route card. The file extension will set the type of file output. Supported extensions are
              currently: xlsx and csv. The default is """+DEFAULT_OUTPUT_FILE
parser.add_argument("-o", "--output", help=help_msg, default=DEFAULT_OUTPUT_FILE)
help_msg = """The number of figures included in the grid reference. 10 figures is 1 m precision. 8 figures is 10 m precision. 
              The default is """+str(DEFAULT_GRID_FIGS)+" figure grid reference"
parser.add_argument("-g", "--grid", help=help_msg, default=DEFAULT_GRID_FIGS)
help_msg = """The card point flag. Tells the program what piece of text indicates that a point should appear in the
              route card. This piece of text can appear in the name, description or comment of a route point or track point.
              The default is """ + DEFAULT_CARD_POINT_FLAG
parser.add_argument("-f", "--flag", help=help_msg, default=DEFAULT_CARD_POINT_FLAG)
help_msg="""The contour interval that elevation is rounded to, in meters, for calculating elevation difference. 
            The default value is """ + str(DEFAULT_ELE_BAND_WIDTH)
parser.add_argument("-i", "--interval", help=help_msg, default=DEFAULT_ELE_BAND_WIDTH)
help_msg="""The height past a contour interval to count as in that contour interval. 
            The default value is 1/5 the contour interval height"""
parser.add_argument("-b", "--buffer", help=help_msg, default=AUTO_ELE_BUFFER)

args = parser.parse_args()
create_route_card(args.gpx_file, args.output, figs_grid_ref=args.grid, card_point_flag=args.flag,\
                  ele_band_width=args.interval, ele_buffer=args.buffer)
