from basicgeo import P3, AlongAcc, I1
import stlgenerator

class TriangleNode:   # replace with just P3
    def __init__(self, p, i):
        self.p = p
        self.i = i  # index
        

class TriangleBar:
    def __init__(self, nodeback, nodefore):
        self.nodeback = nodeback
        self.nodefore = nodefore
        self.barforeright = None
        self.barbackleft = None
        self.i = -1 # index
        assert nodefore.i > nodeback.i
        
    def SetForeRightBL(self, bforeright, bar):
        if bforeright:
            self.barforeright = bar
        else:
            self.barbackleft = bar

    def GetForeRightBL(self, bforeright):
        if bforeright:
            return self.barforeright
        else:
            return self.barbackleft
            
    def GetNodeFore(self, bfore):
        if bfore:
            return self.nodefore
        else:
            return self.nodeback

    def DGetCellMarkRightL(self, bright):
        if bright:
            return self.cellmarkright
        else:
            return self.cellmarkleft

    def DIsTriangleRefBar(self):
        return self.barforeright and (self.barforeright.GetNodeFore(self.nodefore == self.barforeright.nodeback).i > self.nodeback.i)
        

class TriangleBarMesh:
    def __init__(self, fname=None, trans=None, nodesortkey=lambda X:X):
        self.nodes = [ ]
        self.bars = [ ]
        self.nodesortkey = nodesortkey
        #self.xlo, self.xhi, self.ylo, self.yhi  # set in NewNode()

        if fname is not None:
            sr = stlgenerator.stlreader(fname, trans)
            self.BuildTriangleBarmesh(sr)
            r0 = max(map(abs, (self.xlo, self.xhi, self.ylo, self.yhi, self.zlo, self.zhi)))
            assert r0 < 100000, ("triangles too far from origin", r0)
            #sendactivity("triangles", codetriangles=tbm.GetBarMeshTriangles())
        
    def GetNodePoint(self, i):
        return self.nodes[i].p
    def GetBarPoints(self, i):
        bar = self.bars[i]
        return (bar.nodeback.p, bar.nodefore.p)
    def GetTriPoints(self, i):
        bar = self.bars[i]
        node2 = bar.barforeright.GetNodeFore(bar.nodefore == bar.barforeright.nodeback)
        return (bar.nodeback.p, bar.nodefore.p, node2.p)
        
    def NewNode(self, p):
        if self.nodes:
            if p.x < self.xlo:  self.xlo = p.x
            if p.x > self.xhi:  self.xhi = p.x
            if p.y < self.ylo:  self.ylo = p.y
            if p.y > self.yhi:  self.yhi = p.y
            if p.z < self.zlo:  self.zlo = p.z
            if p.z > self.zhi:  self.zhi = p.z
        else:
            self.xlo = self.xhi = p.x
            self.ylo = self.yhi = p.y
            self.zlo = self.zhi = p.z
        self.nodes.append(TriangleNode(p, len(self.nodes)))
        return self.nodes[-1]

        
    # possibly should be a completely separate class, even though it reuses the same topological structure things
    def BuildTriangleBarmesh(self, trpts):
        # strip out duplicates in the corner points of the triangles
        ipts, jtrs = [ ], [ ]
        for i, tr in enumerate(trpts):
            ipts.append((tr[0:3], i*3+0))
            ipts.append((tr[3:6], i*3+1))
            ipts.append((tr[6:9], i*3+2))
            jtrs.append([-1, -1, -1])
            
        ipts.sort(key=self.nodesortkey)
        prevpt = None
        for pt, i3 in ipts:
            if not prevpt or prevpt != pt:
                self.NewNode(P3(pt[0], pt[1], pt[2]))
                prevpt = pt
            jtrs[i3 // 3][i3 % 3] = len(self.nodes) - 1
        del ipts
        
        # create the barcycles around each triangle
        tbars = [ ]
        for jt0, jt1, jt2 in jtrs:
            if jt0 != jt1 and jt0 != jt2 and jt1 != jt2:  # are all the points distinct?
                tbars.append(jt0 < jt1 and TriangleBar(self.nodes[jt0], self.nodes[jt1]) or TriangleBar(self.nodes[jt1], self.nodes[jt0]))
                tbars.append(jt1 < jt2 and TriangleBar(self.nodes[jt1], self.nodes[jt2]) or TriangleBar(self.nodes[jt2], self.nodes[jt1]))
                tbars.append(jt2 < jt0 and TriangleBar(self.nodes[jt2], self.nodes[jt0]) or TriangleBar(self.nodes[jt0], self.nodes[jt2]))
                tbars[-3].SetForeRightBL(jt0 < jt1, tbars[-2]) 
                tbars[-2].SetForeRightBL(jt1 < jt2, tbars[-1]) 
                tbars[-1].SetForeRightBL(jt2 < jt0, tbars[-3]) 
        del jtrs
        
        # strip out duplicates of bars where two triangles meet
        tbars.sort(key=lambda bar: (bar.nodeback.i, bar.nodefore.i, not bar.barbackleft))
        prevbar = None
        for bar in tbars:
            if prevbar and prevbar.nodeback == bar.nodeback and prevbar.nodefore == bar.nodefore and \
                    prevbar.barbackleft and not prevbar.barforeright and not bar.barbackleft and bar.barforeright:
                prevbar.barforeright = bar.barforeright
                node2 = bar.barforeright.GetNodeFore(bar.nodefore == bar.barforeright.nodeback)
                bar2 = bar.barforeright.GetForeRightBL(bar.nodefore == bar.barforeright.nodeback)
                assert bar2.GetNodeFore(bar2.nodeback == node2) == bar.nodeback
                assert bar2.GetForeRightBL(bar2.nodeback == node2) == bar
                bar2.SetForeRightBL(bar2.nodeback == node2, prevbar)
                prevbar = None
            else:
                prevbar = bar
                assert prevbar.i == -1
                prevbar.i = len(self.bars)
                self.bars.append(bar)
        del tbars
        

    def GetBarMeshTriangles(self):
        tris = [ ]
        for bar in self.bars:
            if bar.barforeright:
                node2 = bar.barforeright.GetNodeFore(bar.nodefore == bar.barforeright.nodeback)
                if node2.i > bar.nodeback.i:
                    node0 = bar.nodeback
                    node1 = bar.nodefore
                    tris.append((node0.p.x, node0.p.y, node0.p.z, node1.p.x, node1.p.y, node1.p.z, node2.p.x, node2.p.y, node2.p.z))
        return tris
        
    def GetFacts(self):
        ntriangles = 0
        nsinglesidededges = 0
        for bar in self.bars:
            if bar.barforeright:
                node2 = bar.barforeright.GetNodeFore(bar.nodefore == bar.barforeright.nodeback)
                if node2.i > bar.nodeback.i:
                    ntriangles += 1
                if not bar.barbackleft:
                    nsinglesidededges += 1
            else:
                nsinglesidededges += 1
        return (len(self.nodes), len(self.bars), ntriangles, nsinglesidededges)
        
            

