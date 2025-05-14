import gpxpy
import pyproj
import numpy as np

class route_point:
    def __init__(self, gpx_point, transformer):
        self.elevation = gpx_point.elevation
        self.card_point_flag = check_if_card_point(gpx_point, "wp")
        self.x, self.y = transformer.transform(gpx_point.latitude, gpx_point.longitude) 
        self.dist_from_prev  = 0
        self.ascent_from_prev  = 0
        self.decent_from_prev  = 0
    def join_to(self, prev_point):
        self.dist_from_prev = np.sqrt((self.x-prev_point.x)**2 + (self.y-prev_point.y)**2)
        elevation_change = self.elevation - prev_point.elevation
        if elevation_change > 0:
            self.ascent_from_prev  = elevation_change
        else:
            self.decent_from_prev  = elevation_change

class card_point:
    def __init__(self, point, points_since_prev_card_point):
        self.elevation = point.elevation
        self.x = point.x
        self.y = point.y
        self.dist_from_prev = 0
        self.ascent_from_prev = 0
        self.decent_from_prev = 0

        for point in points_since_prev_card_point[1::]:
            self.dist_from_prev += point.dist_from_prev 
            self.ascent_from_prev += point.ascent_from_prev 
            self.decent_from_prev += point.decent_from_prev 

        prev_card_point = points_since_prev_card_point[0]
        slope = (self.y-prev_card_point.y)/(self.x-prev_card_point.x)
        self.grid_bearing = (90 - np.arctan(slope)*180/np.pi) % 360 # ERROR HERE- need to sort out if going West

        self.dist_accumulative = 0
        self.ascent_accumulative = 0
        self.decent_accumulative = 0


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

def import_gpx_file(filename):
    # read route into array of point objects from the gpxpy module 
    gpx_file = open(filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    gpx_file.close()
    gpx_points = extract_path(gpx)
    num_gpx_points = len(gpx_points)

    # convert to irish grid coordinates, calculate parameters and store as route_point objects
    global_coords = pyproj.Proj("epsg:4326")
    irish_grid = pyproj.Proj("epsg:29902")
    global_coords_to_irish_grid = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:29902")
    full_route = [route_point(point, global_coords_to_irish_grid) for point in gpx_points]
    for i in range(1, num_gpx_points): full_route[i].join_to(full_route[i-1])
    
    # create array of just points that should appear on the route card and calculate parameters
    card_point_index = 0
    card_points = []
    for i in range(1, num_gpx_points):
        if not (full_route[i].card_point_flag or i==num_gpx_points-1):
            continue
        prev_card_point_index = card_point_index
        card_point_index = i
        card_points.append(card_point(full_route[i], full_route[prev_card_point_index:i+1]))
    
    temp = 0    
    for i in card_points:
        temp += i.dist_from_prev
    print(card_points[len(card_points)-1].grid_bearing)

import_gpx_file("test.gpx")
