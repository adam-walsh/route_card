import route_card
import argparse

parser = argparse.ArgumentParser(description= """
Creates a route card from a gpx file. The fields in the route card it makes are: 
Grid Reference, Distance, Ascent, Descent, Compass Bearing	Total Distance, Total Ascen, Total Descent.
Your route card should also have timing information but this programme doesn't do that for you. Do that yourself.
""")

help_msg = """The filename of the gpx file containing the route. Points must have the card point flag for the programme to
              add them to the route card."""
parser.add_argument("gpx_file", help=help_msg)
help_msg = """The filename for the route card. The file extension will set the type of file output. Supported extensions are
              currently: xlsx and csv. The default is """+route_card.DEFAULT_OUTPUT_FILE
parser.add_argument("-o", "--output", help=help_msg, default=route_card.DEFAULT_OUTPUT_FILE)
help_msg = """The number of figures included in the grid reference. 10 figures is 1 m precision. 8 figures is 10 m precision. 
              The default is """+str(route_card.DEFAULT_GRID_FIGS)+" figure grid reference"
parser.add_argument("-g", "--grid", help=help_msg, default=route_card.DEFAULT_GRID_FIGS)
help_msg = """The card point flag. Tells the program what piece of text indicates that a point should appear in the
              route card. This piece of text can appear in the name, description or comment of a route point or track point.
              The default is """ +route_card.DEFAULT_CARD_POINT_FLAG
parser.add_argument("-f", "--flag", help=help_msg, default=route_card.DEFAULT_CARD_POINT_FLAG)
help_msg="""The contour interval that elevation is rounded to, in meters, for calculating elevation difference. 
            The default value is """ +str(route_card.DEFAULT_ELE_BAND_WIDTH)
parser.add_argument("-i", "--interval", help=help_msg, default=route_card.DEFAULT_ELE_BAND_WIDTH)
help_msg="""The height past a contour interval to count as in that contour interval. 
            The default value is 1/5 the contour interval height"""
parser.add_argument("-b", "--buffer", help=help_msg, default=route_card.AUTO_ELE_BUFFER)

args = parser.parse_args()
route_card.create_route_card(args.gpx_file, args.output, figs_grid_ref=args.grid, card_point_flag=args.flag,\
                  ele_band_width=args.interval, ele_buffer=args.buffer)
