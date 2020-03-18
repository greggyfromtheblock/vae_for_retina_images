from __future__ import division, print_function

import argparse
import os
import random
import warnings

import numpy as np
from skimage import io

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description='Database Image Size Scanner')
parser.add_argument('dir', type=str, default=None, metavar='image_dir',
                    help="""The path to the directory which contains
                    the imgages""")
parser.add_argument('outdir', type=str, default=None, metavar='output_dir',
                    help="""The path of the new directory where 
                    they will be saved""")
parser.add_argument('--resize', type=int, nargs=2, default=[0,0], metavar='resize shape',
                    help="""if resize is desired
                    use this option and give it 2 ints""")
args = parser.parse_args()


# Correcting the possibly missing slash.
# It's lame but works for this little purpose
if args.dir[-1] != '/':
    args.dir += '/'
if args.outdir[-1] != '/':
    args.outdir += '/'

prefix = "preptest"
outdir = "preptest/"
db = 'odir/ODIR-5K_Training_Annotations(Updated)_V2.xlsx'
imdir = 'odir/ODIR-5K_Training_Dataset/'

outdir = args.outdir
imdir = args.dir
os.makedirs(outdir, exist_ok=True)


def trim_image_rgb(img, r=0):
    """Trims the black margins out of the image
    The originaland returned images are rgb"""
    ts = (img != 0).sum(axis=1) != 0
    ts = ts.sum(axis=1) != 0
    img = img[ts]
    ts = (img != 0).sum(axis=0) != 0
    ts = ts.sum(axis=1) != 0
    img = img[:,ts,:]
    if r != [0,0] and r != (0,0) and r !=0:
        img = resize(img, r, anti_aliasing=True)
    return img

# Generate the standardized image set
for f in os.listdir(imdir):
    fname = f.replace(".jpg", "")
    image = io.imread(imdir + f)
    image = trim_image_rgb(image, args.resize)
    image = image.astype(np.uint8)
    io.imsave(outdir + f + "_cropped", image)
