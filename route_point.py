import pyproj
import numpy as np

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
