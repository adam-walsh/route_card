import gpxpy
import pyproj
import numpy as np
import pandas as pd
from datetime import datetime as dt
from pygeomag import GeoMag


ELE_BAND_WIDTH = 5 # resolution of elevation for calculating change in elevation
ELE_HYSTERISIS = ELE_BAND_WIDTH/3

class route_point:
    def __init__(self, gpx_point, transformer, ele_band_prev):
        self.lat, self.lon, self.elevation = gpx_point.latitude, gpx_point.longitude, gpx_point.elevation
        self.card_point_flag = check_if_card_point(gpx_point, "wp")
        self.easting, self.northing = transformer.transform(gpx_point.latitude, gpx_point.longitude) 
        self.dist_from_prev  = self.ascent_from_prev = self.decent_from_prev = 0
        self.elevation_band = discretize_elevation(self.elevation, ele_band_prev)
 
    def join_to(self, prev_point):  # calculate values based off coming from the previous point
        self.dist_from_prev = np.sqrt((self.easting-prev_point.easting)**2 + (self.northing-prev_point.northing)**2)
        elevation_change = self.elevation_band - prev_point.elevation_band
        if elevation_change > 0:
            self.ascent_from_prev  = elevation_change
        else:
            self.decent_from_prev  = elevation_change

class card_point:
    def __init__(self, point, points_since_prev_card_point, prev_card_point, magnetic_variation, earth_model, figs_grid_ref):
        self.grid_ref = irish_grid_ref2map_ref(point.easting, point.northing, figs_grid_ref)
        self.dist_from_prev = self.ascent_from_prev = self.decent_from_prev = 0
        self.lat, self.lon = point.lat, point.lon
        
        if points_since_prev_card_point == "first_point":
            self.compass_bearing = self.dist_from_prev = self.ascent_from_prev = self.decent_from_prev = 0
            self.dist_accumulative = self.ascent_accumulative = self.decent_accumulative = 0
            return
        
        for point in points_since_prev_card_point[1::]:
            self.dist_from_prev += point.dist_from_prev 
            self.ascent_from_prev += point.ascent_from_prev 
            self.decent_from_prev += point.decent_from_prev 
        
        self.dist_accumulative = prev_card_point.dist_accumulative + self.dist_from_prev
        self.ascent_accumulative = prev_card_point.ascent_accumulative + self.ascent_from_prev
        self.decent_accumulative = prev_card_point.decent_accumulative + self.decent_from_prev

        grid_bearing = earth_model.inv(prev_card_point.lon, prev_card_point.lat, point.lon, point.lat)[0]
        self.compass_bearing = (grid_bearing + magnetic_variation)%360
    
def irish_grid_ref2map_ref(easting, northing, figs_grid_ref):
    irish_grid_letter_layout = [['a', 'b', 'c', 'd', 'e'],
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

def discretize_elevation(elevation, prev_elevation_band):
        if elevation > prev_elevation_band + ELE_BAND_WIDTH + ELE_HYSTERISIS:
            return (elevation - ELE_HYSTERISIS) // ELE_BAND_WIDTH * ELE_BAND_WIDTH
        elif elevation < prev_elevation_band - ELE_BAND_WIDTH - ELE_HYSTERISIS:
            return (elevation + ELE_HYSTERISIS) // ELE_BAND_WIDTH * ELE_BAND_WIDTH
        else:
            return prev_elevation_band

def check_if_card_point(gpx_point, card_point_marker):
    possible_marker_locations = [gpx_point.name, gpx_point.comment, gpx_point.description]
    for i in possible_marker_locations:
        if not (isinstance(i, str)):
            continue
        if card_point_marker in i:
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

def mag_var_at_start(lat, lon, ele):
    dt_time = dt.today()
    gm_time = dt_time.year + dt_time.month*1/12
    geo_mag = GeoMag(coefficients_file="wmm/WMM_2025.COF")
    mag_var = geo_mag.calculate(glat=lat, glon=lon, alt=ele, time=gm_time).d
    return mag_var

def full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref):
    model = pyproj.Geod(ellps='clrk66')
    card_points = [card_point(full_route[0], "first_point", 0, 0, 0, figs_grid_ref)]
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
                        "decent_from_prev":"Decent[m]",
                        "elevation":"Elevation [m]",
                        "compass_bearing":"Compass Bearing",
                        "ascent_accumulative":"Total Ascent [m]",
                        "decent_accumulative":"Total Decent [m]",
                        "dist_accumulative":"Total Distance [m]"}

    df = df.rename(columns=new_column_names)
    return df

def write_df_to_output(df, output_filename):
    df.to_excel(output_filename)

def create_route_card(input_filename, output_filename, figs_grid_ref):
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
    starting_elevation_band = gpx_points[0].elevation // ELE_BAND_WIDTH * ELE_BAND_WIDTH
    full_route = [0]*num_gpx_points
    full_route[0] = route_point(gpx_points[0], global_coords_to_irish_grid, starting_elevation_band) 
    for i in range(1, num_gpx_points):
        full_route[i] = route_point(gpx_points[i], global_coords_to_irish_grid, full_route[i-1].elevation_band) 
    for i in range(1, num_gpx_points): full_route[i].join_to(full_route[i-1])
    
    # create array of just points that should appear on the route card and calculate parameters
    card_points = full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref)
    df = array2df(card_points)

    write_df_to_output(df, output_filename)
           
create_route_card("test.gpx", "/mnt/c/Users/adamm/Documents/output.xlsx", 6)
