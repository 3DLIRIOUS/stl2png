import re, struct, math, sys

def stlreader(fname, trans=None):
    if trans is None:
        trans = lambda p:p
    if trans == 'INCH':
        trans = lambda p: (p[0]*25.4, p[1]*25.4, p[2]*25.4)

    fin = open(fname, "r")
    try:
        l = fin.read(1024)
        bascii = l[:5] == "solid" and not re.search("[^A-Za-z0-9_%\,\.\/\;\:\'\"\+\-\s\r\n]", l[6:])
        fin.seek(0)
    except UnicodeDecodeError:
        bascii = False
       
    little_endian = (struct.unpack("<f", struct.pack("@f", 140919.00))[0] == 140919.00)
    nfacets = 0
    ndegenerate = 0
    
    if bascii:
        trpts = []
        for l in fin:
            l = l.replace(",", ".") # Catia writes ASCII STL with , as decimal point
            if re.search("facet", l) or re.search("outer", l) or re.search("endloop", l) or re.search("endfacet", l):
                continue
            tpl = re.search("vertex\s*([\d\-\+\.EeDd]+)\s*([\d\-\+\.EeDd]+)\s*([\d\-\+\.EeDd]+)", l)
            if tpl:
                trpts.extend(trans(list(map(float, tpl.groups()))))
            if len(trpts) == 9:
                yield trpts
                nfacets += 1
                trpts = []
        return
    
    fin = open(fname, "rb")
    hdr = fin.read(80)  # 80 bytes of header
    hnfacets = struct.unpack("<i", fin.read(4))[0]
    nfacets = 0
    while True:
        fin.read(12) # override normal
        try:
            trpts = struct.unpack("<9f", fin.read(36)) # little endian
            assert len(trpts) == 9, len(trpts)
            trpts = trans(trpts[0:3])+trans(trpts[3:6])+trans(trpts[6:9])
        except struct.error as e:
            break
        yield trpts
        fin.read(2) # padding
        nfacets += 1
    
if __name__ == "__main__":
    sendactivity("clearalltriangles")
    def swapyz(t):
        return (t[0], -t[2], t[1] - 3)
    sr = stlreader("/home/goatchurch/geom3d/stlfiles/impellor1.stl", trans=swapyz)
    sendactivity("triangles", codetriangles=list(sr))
