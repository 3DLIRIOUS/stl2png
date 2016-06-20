# Description #

This program is for generating black and while png files from an STL file at a particular z height.



The code is written is self-contained (including the STL reader and PNG writer) and is written in 
pure Python, so it can be run under pypy for greater speed -- though it runs pretty quickly at the moment 
in spite of no code optimization having been applied.

The original files are extracted from a larger project called [barmesh](https://bitbucket.org/goatchurch/barmesh) 
that can be used for generating contour slices of an STL file for a given diameter tool.

Usage: stl2png.py [options]

Slices STL files into black and white PNG bitmaps as a batch or on demand

Options:
  -h, --help            show this help message and exit
  -s FILE, --stl=FILE   Input STL file
  -o FILE, --output=FILE
                        Output image name (can contain %d or %f) for multiple
                        names
  -t TRANSFORM, --transform=TRANSFORM
                        Transformation to apply to STL file
  -q, --quiet           Verbose
  -w WIDTHPIXELS, --width=WIDTHPIXELS
                        Bitmap width
  --height=HEIGHTPIXELS
                        Bitmap height
  --extra=EXTRA         Extra space to leave around the model
  -p POSITION, --position=POSITION
                        Position
  -n NSLICES, --nslices=NSLICES
                        Number of slices to make
  -z ZLEVELS, --zlevel=ZLEVELS
                        Zlevel values to slice at
  -i, --inputs          Wait for lines from input stream of form 'zvalue
                        [pngfile]\n'

For more speed try running with pypy


# License #

This code is released under [BSD license](http://choosealicense.com/licenses/bsd-2-clause/), 
which permits you to do anything you like with it except blame me for the consequences.



