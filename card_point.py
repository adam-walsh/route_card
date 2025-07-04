import pyproj
import numpy as np

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
        
        for route_point in points_since_prev_card_point[1::]:
            self.dist_from_prev += route_point.dist_from_prev 
            self.ascent_from_prev += route_point.ascent_from_prev 
            self.descent_from_prev += route_point.descent_from_prev 
        
        self.dist_accumulative = prev_card_point.dist_accumulative + self.dist_from_prev
        self.ascent_accumulative = prev_card_point.ascent_accumulative + self.ascent_from_prev
        self.descent_accumulative = prev_card_point.descent_accumulative + self.descent_from_prev

        # note the bearing is from true north not grid north
        true_bearing = earth_model.inv(prev_card_point.lon, prev_card_point.lat, point.lon, point.lat)[0]
        self.compass_bearing = (true_bearing + magnetic_variation)%360
    

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

# takes the full route and forms an array of points to be put on the route card
def full_route2route_card(full_route, mag_var, num_gpx_points, figs_grid_ref):
    model = pyproj.Geod(ellps='clrk66')
    card_points = [card_point(full_route[0], 0, 0, "first_point", 0, figs_grid_ref)]
    card_point_index = 0
    for i in range(1, num_gpx_points):
        if not (full_route[i].card_point_flag or i==num_gpx_points-1):
            continue
        prev_card_point_i = card_point_index
        card_point_index = i
        prec_card_point = card_points[-1:][0]
        cp = card_point(full_route[i], full_route[prev_card_point_i:i+1], card_points[-1:][0], mag_var, model, figs_grid_ref)
        card_points.append(cp)
    return card_points
