import gpxpy
import pyproj
import numpy as np
import pandas as pd
from datetime import datetime as dt
from pygeomag import GeoMag

import route_point as rp
import card_point as cp

# constants whose values whould not be changed after this block
# ==============================================================================================================================
DEFAULT_GRID_FIGS = 6   # by default a 6 figure grid reference is used
DEFAULT_ELE_BAND_WIDTH = 5 # resolution of elevation for calculating change in elevation in meters
AUTO_ELE_BUFFER = -1   # tells the function to set the elevation buffer itself. Used with band width for changes in elevation
DEFAULT_CARD_POINT_FLAG = "cp" # the string that tells the programme to include a point in the route card
DEFAULT_OUTPUT_FILE = r"route_card.csv"
GLOABL_COORDS = "EPSG:4326" # wgs 84, normal longitude and latitude gloabl coordinates
IRISH_GRID = "EPSG:29902"   # irish national grid coordinates. The one that's just numbers, no letters
# ==============================================================================================================================

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

def extract_path(input_filename):
    gpx_file = open(input_filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    gpx_file.close()
    num_tracks = len(gpx.tracks)
    num_routes = len(gpx.routes)
    if check_for_track(num_tracks, num_routes):
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
    gpx_points = extract_path(input_filename)
    num_gpx_points = len(gpx_points)

    # convert to irish grid coordinates, calculate parameters and store as route_point objects
    mag_var = mag_var_at_start(gpx_points[0].latitude, gpx_points[0].longitude, gpx_points[0].elevation)
    global_coords_to_irish_grid = pyproj.Transformer.from_crs(GLOABL_COORDS, IRISH_GRID)
    starting_elevation_band = gpx_points[0].elevation // ele_band_width * ele_band_width 
    full_route = np.empty(num_gpx_points, dtype=rp.route_point) 
    full_route[0] = rp.route_point(gpx_points[0], global_coords_to_irish_grid, starting_elevation_band,\
                                card_point_flag, ele_band_width, ele_buffer) 
    for i in range(1, num_gpx_points):
        full_route[i] = rp.route_point(gpx_points[i], global_coords_to_irish_grid, full_route[i-1].elevation_band,\
        card_point_flag, ele_band_width, ele_buffer) 

    for i in range(1, num_gpx_points): 
        full_route[i].join_to(full_route[i-1])
   
    # create array of just points that should appear on the route card and calculate parameters
    card_points = cp.full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref)
    df = array2df(card_points)

    write_df_to_output(df, output_filename)
