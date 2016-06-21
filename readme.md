# Description #

This program is for generating black and while PNG files from an STL file at particular z heights.

It has applications to [SLA stereolithography](http://3dprintingfromscratch.com/common/types-of-3d-printers-or-3d-printing-technologies-overview/#sla) where a projector shines an image upwards 
through the base of a glass dish filled with a liquid that solidifies where the light touches it.  
The solid printed part is drawn upwards out of the liquid like the reverse of melting ice.

The **-i** option allows for the printer driver to request a slice image from this program 
repeatedly in realtime at any particular z height so that the set of images don't need to be 
calculated in advance and managed in an array of predefined layer heights.  In this way the 
system can be configured to generate a new image up to ten times a second so that the 
vertical resolution of the print will only depend only on the speed of the process, which can 
be varied during the build itself.

The slicer can take more than one STL file at a time and merge them into the same image.  
The second STL file, for example, could contain the support material structures so it  
doesn't need to be merged with the original model (a very non-trivial 
3D operation).  

The code is self-contained (including the STL reader and PNG writer) and is written in 
pure Python so it can be run under pypy for greater speed (though it runs pretty quickly at the moment). 

The original source code has been extracted from a larger project called [barmesh](https://bitbucket.org/goatchurch/barmesh) 
by the author.

# Command line options #

eg:
  **python stl2png.py -s file.stl --nslices=10**
(or run as pypy stl2png.py for more speed)

```
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
```

# Design #

The STL file format is so trivial that both its ascii and binary forms can be parsed in less than 
50 lines of Python code.  This produces a list of 9-tuples defining the triangles 
which is read into TriangleBarMesh where the duplicated points and edges are 
joined to create a connected manifold.  This manifold model knows which two triangles 
are on either side of each edge -- assuming that the surface is properly closed with no free edges.  

For a slice to be made, all the edges that span the z-value of the slice are identified and 
the point intersection with the horizontal z-plane is calculated.  Since the triangles on either side of 
each edge are known, the pairs of points that need to be joined to represent the line intersection 
of the triangle with the z-plane are easily identified.  

There is a list of intersections (the ycuts) between each raster line of constant y in the final bitmap and 
this set of line slices of triangles (that should form a set of closed contours).  This models the 
output image before it is written into file using a lightweight implementation of 
the PNG format in less than 40 lines of Python.  

# Known issues #

The bitmap image might be upside down because PNG raster lines start from the top and work towards 
the bottom in the opposite direction to the conventional y-coordinate direction.  
Simply flipping the order of the raster lines could be complicated by the fact that the yhi value 
is varied to keep the aspect ratio of a pixel constant.  

There aren't any working features for controlling the absolute position and scale of the image 
pixels in relation to the coordinate space of the STL file.  The development of such features 
are best left to when this program is in use within another system so that it can adhere to its design.

The originally intended optimizations have not been implemented as it was discovered that 
this simpler version runs pretty fast already, even for code that would conventionally 
have been written in C++.

# License #

This code is released under [BSD license](http://choosealicense.com/licenses/bsd-2-clause/), 
which permits you to do anything you like with it except blame me for the consequences.