#
# Executes the rendering process jobs on the cluster (based on Rhoana's driver).
# It takes a collection of tilespec files, each describing a montage of a single section,
# where all sections are aligned to a single coordinate system,
# and outputs a per-section image (or images/tiles).
# The input is a directory with tilespec files in json format (each file for a single layer).
#

import sys
import os.path
import os
import subprocess
import datetime
import time
from collections import defaultdict
import argparse
import glob
import json
from render import render_tilespec
from utils import create_dir, read_layer_from_file, parse_range
from rh_aligner.common.bounding_box import BoundingBox
import math

###############################
# Driver
###############################
if __name__ == '__main__':



    # Command line parser
    parser = argparse.ArgumentParser(description='Renders a given set of images using the SLURM cluster commands.')
    parser.add_argument('tiles_dir', metavar='tiles_dir', type=str, 
                        help='a directory that contains a tile_spec files in json format')
    parser.add_argument('-o', '--output_dir', type=str,
                        help='the directory where the rendered output files will be stored (default: ./output)',
                        default='./output')
    parser.add_argument('--scale', type=float,
                        help='set the scale of the rendered images (default: full image)',
                        default=1.0)
    #parser.add_argument('--from_layer', type=int,
    #                    help='the layer to start from (inclusive, default: the first layer in the data)',
    #                    default=-1)
    #parser.add_argument('--to_layer', type=int,
    #                    help='the last layer to render (inclusive, default: the last layer in the data)',
    #                    default=-1)
    parser.add_argument('--from_x', type=int,
                        help='the left coordinate (default: 0)',
                        default=0)
    parser.add_argument('--from_y', type=int,
                        help='the top coordinate (default: 0)',
                        default=0)
    parser.add_argument('--to_x', type=int,
                        help='the right coordinate (default: full image)',
                        default=-1)
    parser.add_argument('--to_y', type=int,
                        help='the bottom coordinate (default: full image)',
                        default=-1)
    parser.add_argument('--tile_size', type=int,
                        help='the size (square side) of each tile (default: 0 - whole image)',
                        default=0)
    parser.add_argument('--output_type', type=str,
                        help='The output type format',
                        default='png')
    parser.add_argument('-i', '--invert_image', type=bool,
                        help='store an inverted image',
                        default=True)
    #parser.add_argument('-s', '--skip_layers', type=str, 
    #                    help='the range of layers (sections) that will not be processed e.g., "2,3,9-11,18" (default: no skipped sections)',
    #                    default=None)
    parser.add_argument('-k', '--keeprunning', action='store_true', 
                        help='Run all jobs and report cluster jobs execution stats')
    parser.add_argument('-m', '--multicore', action='store_true', 
                        help='Run all jobs in blocks on multiple cores')
    parser.add_argument('-mk', '--multicore_keeprunning', action='store_true', 
                        help='Run all jobs in blocks on multiple cores and report cluster jobs execution stats')

    args = parser.parse_args()


    create_dir(args.output_dir)


    all_files = glob.glob(os.path.join(args.tiles_dir, '*.json'))
    if len(all_files) == 0:
        print "No json files to render, quitting"
        sys.exit(1)

    print "Computing entire 3d volume bounding box"
    # Compute the width and height of the entire 3d volume
    # so all images will have the same dimensions (needed for many image viewing applications, e.g., Fiji)
    entire_image_bbox = BoundingBox.read_bbox_grep(all_files[0])
    for in_fname in all_files[1:]:
        entire_image_bbox.extend(BoundingBox.read_bbox_grep(in_fname))
    print "Final bbox for the 3d image: {}".format(entire_image_bbox)

    # Set the boundaries according to the entire_image_bbox
    if args.from_x == 0:
        args.from_x = int(math.floor(entire_image_bbox[0]))
    if args.from_y == 0:
        args.from_y = int(math.floor(entire_image_bbox[2]))
    if args.to_x == -1:
        args.to_x = int(math.ceil(entire_image_bbox[1]))
    if args.to_y == -1:
        args.to_y = int(math.ceil(entire_image_bbox[3]))

    # Set the max_col and max_row (in case of rendering tiles)
    max_col = 0
    max_row = 0
    if not args.tile_size == 0:
        max_col = int(math.ceil((args.to_x - args.from_x) / float(args.tile_size)))
        max_row = int(math.ceil((args.to_y - args.from_y) / float(args.tile_size)))

    # Render each section to fit the out_shape
    for in_fname in all_files:
        if args.tile_size == 0:
            # Single image (no tiles)
            out_fname_prefix = os.path.splitext(os.path.join(args.output_dir, os.path.basename(in_fname)))[0]
            out_fname = "{}.{}".format(out_fname_prefix, args.output_type)

            # match the features of neighboring tiles
            if not os.path.exists(out_fname):
                print "Rendering section {}".format(in_fname)
                job_render = render_tilespec(in_fname, out_fname, args.scale, args.output_type, (args.from_x, args.to_x, args.from_y,  args.to_y), args.tile_size, args.invert_image)
        else:
            # Multiple tiles should be at the output (a single directory per section)
            tiles_out_dir = os.path.splitext(os.path.join(args.output_dir, os.path.basename(in_fname)))[0]
            create_dir(tiles_out_dir)
            out_fname_prefix = os.path.splitext(os.path.join(tiles_out_dir, os.path.basename(in_fname)))[0]

            # Check if the last file is in the output directory
            last_file = '{}_tr{}-tc{}.{}'.format(out_fname_prefix, max_row + 1, max_col + 1, args.output_type)
            if not os.path.exists(last_file):
                print "Rendering Tiled section {}".format(in_fname)
                job_render = render_tilespec(in_fname, out_fname_prefix, args.scale, args.output_type, (args.from_x, args.to_x, args.from_y, args.to_y), args.tile_size, args.invert_image)
