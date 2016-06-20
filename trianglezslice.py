from basicgeo import P2, P3, Partition1, Along
from trianglebarmesh import TriangleBarMesh
import zlib, struct, time

class TriZSlice:
    def __init__(self, optionverbose):
        self.optionverbose = optionverbose
        self.tbms = [ ]  # multiple stlfiles will be unioned together
                         # eg like support material structures, 
                         # though these may have a better definition than triangle files
                         # such as branching lines and variable offset radii
        
    def LoadSTLfile(self, stlfile, transmap):
        tbm = TriangleBarMesh(stlfile, transmap, nodesortkey=lambda X:(X[0][2], X[0][1], X[0][0], X[1]))  # every edge has nodefrom.p.z<=nodeto.p.z
        if self.optionverbose:
            nnodes, nedges, ntriangles, nsinglesidededges = tbm.GetFacts()
            print("%s:  nodes=%d edges=%d triangles=%d singlesidededges=%d" % (stlfile, nnodes, nedges, ntriangles, nsinglesidededges))
            if nsinglesidededges != 0:
                print("*** Warning, not a closed surface")
        self.tbms.append(tbm)

    def SetExtents(self, optionextra):
        self.xlo, self.xhi = min(tbm.xlo  for tbm in self.tbms), max(tbm.xhi  for tbm in self.tbms)
        self.ylo, self.yhi = min(tbm.ylo  for tbm in self.tbms), max(tbm.yhi  for tbm in self.tbms)
        self.zlo, self.zhi = min(tbm.zlo  for tbm in self.tbms), max(tbm.zhi  for tbm in self.tbms)
        if self.optionverbose:
            print("Dimensions: xlo=%.3f xhi=%.3f  ylo=%.3f yhi=%.3f  zlo=%.3f zhi=%.3f" % (self.xlo, self.xhi, self.ylo, self.yhi, self.zlo, self.zhi))
        if optionextra[-1] == "%":
            expc = float(optionextra[:-1])
            xex = (self.xhi-self.xlo)*expc/100
            yex = (self.yhi-self.ylo)*expc/100
        else:
            xex = float(optionextra)
            yex = float(optionextra)
        self.xlo -= xex;  self.xhi += xex
        self.ylo -= yex;  self.yhi += yex
        
        
    def BuildPixelGridStructures(self, optionwidthpixels, optionheightpixels):
        # grids partitions defining the interval width of each pixel
        self.xpixels = Partition1(self.xlo, self.xhi, optionwidthpixels)
        if optionheightpixels == 0:
            heightpixels = int(optionwidthpixels/(self.xhi - self.xlo)*(self.yhi - self.ylo) + 1)
            newyhi = heightpixels*(self.xhi - self.xlo)/optionwidthpixels + self.ylo
            if self.optionverbose:
                print("Revising yhi from %.3f to %.3f to for a whole number of pixels" % (self.yhi, newyhi))
            self.yhi = newyhi
        else:
            heightpixels = optionheightpixels
        self.ypixels = Partition1(self.ylo, self.yhi, heightpixels)

        xpixwid = self.xpixels.vs[1] - self.xpixels.vs[0]
        ypixwid = self.ypixels.vs[1] - self.ypixels.vs[0]
        
        if self.optionverbose:
            print("numxpixels=%d  each width=%.3f  x0=%0.3f" % (self.xpixels.nparts, xpixwid, self.xpixels.vs[0]))
            print("numypixels=%d  each height=%.3f  y0=%0.3f" % (self.ypixels.nparts, ypixwid, self.ypixels.vs[0]))
        
        # partitions with interval boundaries down middle of each pixel with extra line each side for convenience
        self.xpixmidsE = Partition1(self.xlo - xpixwid*0.5, self.xhi + xpixwid*0.5, self.xpixels.nparts + 1)
        self.ypixmidsE = Partition1(self.ylo - ypixwid*0.5, self.yhi + ypixwid*0.5, self.ypixels.nparts + 1)

    def CalcPixelYcuts(self, z, tbm):
        tbarpairs = [ ]
        barcuts = { }
        for bar in tbm.bars:   # bucketing could speed this up
            assert bar.nodeback.p.z <= bar.nodefore.p.z
            if bar.nodeback.p.z <= z < bar.nodefore.p.z:
                bar1 = bar.barforeright
                node2 = bar1.GetNodeFore(bar1.nodeback == bar.nodefore)
                barC = bar1 if node2.p.z <= z else bar1.GetForeRightBL(bar1.nodeback == bar.nodefore)
                tbarpairs.append((bar.i, barC.i))
                
                lam = (z - bar.nodeback.p.z)/(bar.nodefore.p.z - bar.nodeback.p.z)
                cx = Along(lam, bar.nodeback.p.x, bar.nodefore.p.x)
                cy = Along(lam, bar.nodeback.p.y, bar.nodefore.p.y)
                barcuts[bar.i] = P2(cx, cy)

        ycuts = [ []  for iy in range(self.ypixels.nparts) ]  # plural for set of all raster rows
        for i, i1 in tbarpairs:
            p0, p1 = barcuts[i], barcuts[i1]
            iyl, iyh = self.ypixmidsE.GetPartRange(min(p0.v, p1.v), max(p0.v, p1.v))
            for iy in range(iyl, iyh):
                yc = self.ypixmidsE.vs[iy+1]
                assert (p0.v < yc) != (p1.v < yc)
                lam = (yc - p0.v)/(p1.v - p0.v)
                xc = Along(lam, p0.u, p1.u)
                ycuts[iy].append(xc)

        return ycuts
        
    def ConsolidateYCutSingular(self, ycutlist):
        Lycuts = [ ]
        for i, ycuts in enumerate(ycutlist):
            ycuts.sort()
            for j, yc in enumerate(ycuts):
                Lycuts.append((yc, i, (j%2==1)))
        Lycuts.sort()
        Li = set()
        ysegs = [ ]
        yclo = -1.0
        for yc, i, bout in Lycuts:
            if bout:
                Li.remove(i)
                if len(Li) == 0:
                    ychi = yc
                    ysegs.append((yclo, ychi))
            else:
                if len(Li) == 0:
                    yclo = yc
                assert i not in Li
                Li.add(i)
        assert len(Li) == 0
        return ysegs

    def CalcYsegrasters(self, z):
        ysegrasters = [ ]
        ycutsList = [ self.CalcPixelYcuts(z, tbm)  for tbm in self.tbms ]
        for iy in range(self.ypixels.nparts):  # work through each raster line across the list of stlfiles
            ycutlist = [ ycuts[iy]  for ycuts in ycutsList ]
            ysegs = self.ConsolidateYCutSingular(ycutlist)
            ysegrasters.append(ysegs)
        return ysegrasters
        
    def CalcNakedCompressedBitmap(self, ysegrasters):
        compressor = zlib.compressobj()
        lcompressed = []
        def addcompressl(s):
            c = compressor.compress(s)
            if c:
                lcompressed.append(c)
        blackline = b"\0"*(self.xpixels.nparts+1)
        whiteline = b"\xFF"*self.xpixels.nparts
        assert len(ysegrasters) == self.ypixels.nparts
        for ysegs in ysegrasters:
            previxhl = -1  # to get an extra \0 at the start
            for yseg in ysegs:
                ixl, ixh = self.xpixmidsE.GetPartRange(yseg[0], yseg[1])
                addcompressl(blackline[:ixl-previxhl])
                addcompressl(whiteline[:ixh-ixl])
                previxhl = ixh
            addcompressl(blackline[:self.xpixels.nparts-previxhl])
        lcompressed.append(compressor.flush())
        return lcompressed
            
    # this is a very low volume implementation of the PNG standard
    def WritePNG(self, fout, lcompressed):
        widthpixels, heightpixels = self.xpixels.nparts, self.ypixels.nparts
        fout.write(b"\x89" + "PNG\r\n\x1A\n".encode('ascii'))
        colortype, bitdepth, compression, filtertype, interlaced = 0, 8, 0, 0, 0
        block = struct.pack("!I4sIIBBBBB", 13, "IHDR".encode('ascii'), widthpixels, heightpixels, bitdepth, colortype, compression, filtertype, interlaced)
        fout.write(block)
        fout.write(struct.pack("!I", zlib.crc32(block[4:])&0xFFFFFFFF))
        fout.write(struct.pack("!I", sum(map(len, lcompressed))))   # length of compressed data at start of compressed section (which is why it can't be streamed out)
        IDAT = "IDAT".encode('ascii')
        crc = zlib.crc32(IDAT)
        fout.write(IDAT)
        for c in lcompressed:
            crc = zlib.crc32(c, crc)
            fout.write(c)
        fout.write(struct.pack("!I", crc&0xFFFFFFFF))
        block = "IEND".encode('ascii')
        bcrc = zlib.crc32(block)
        fout.write(struct.pack("!I4sI", 0, block, bcrc&0xFFFFFFFF))
        fout.close()

    def SliceToPNG(self, z, pngname):
        stime = time.time()
        ysegrasters = self.CalcYsegrasters(z)
        lcompressed = self.CalcNakedCompressedBitmap(ysegrasters)
        self.WritePNG(open(pngname, "wb"), lcompressed)
        if self.optionverbose:
            print("Sliced at z=%f to file %s  compressbytes=%d %dms" % (z, pngname, sum(map(len, lcompressed)), (time.time()-stime)*1000))
        
        #conts = [ ]
        #for iy, ysegs in enumerate(ysegrasters):
        #    conts.extend([[(yseg[0], tzs.ypixmidsE.vs[iy+1]), (yseg[1], tzs.ypixmidsE.vs[iy+1])]  for yseg in ysegs])
        #sendactivity(contours=conts)

