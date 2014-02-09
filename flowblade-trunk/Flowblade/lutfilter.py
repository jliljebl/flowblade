

CR_BASIS = [[-0.5,  1.5, -1.5,  0.5],
            [ 1.0, -2.5,  2.0, -0.5],
            [-0.5,  0.0,  0.5,  0.0],
            [ 0.0,  1.0,  0.0,  0.0]]

LINEAR_LUT_256 = []
for i in range(0, 256):
    LINEAR_LUT_256.append(i)

class CurvePoint:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

class CRCurve:

    def __init__(self):
        self.CURVES_NUM_POINTS = 17;#this should be enough.
        self.X = 0
        self.Y = 1
        self.points = []
        self.curve = []
        
        self.curve_reset()

    def curve_reset(self):
        self.curve = []
        for i in range(0, 256):
            self.curve.append(i)
        
        self.points = []
        self.set_curve_point(CurvePoint(0, 0))
        self.set_curve_point(CurvePoint(255, 255))

    def set_curve_point(self, new_point):
        if len(self.points) + 1 > self.CURVES_NUM_POINTS:
            return

        for i, p in reversed(list(enumerate(self.points))):
            if p.x == new_point.x:
                self.points.pop(i)

        self.points.append(new_point)
        self.points = sorted(self.points, key=lambda point: point.x) 

    def set_points_from_str(self, points_str):
        points = []
        self.points = points
        self.calculate_curve()

    def get_curve(self, calculate_first):
        if calculate_first:
            self.calculate_curve()
        return self.curve

    def remove_range(self, p1, p2):
        if( p1 > p2 ):
            p1,p2 = p2,p1
        
        for x in range(int(p1), int(p2) + 1):
            self.remove_curve_point(CurvePoint(x, -1))

    def remove_curve_point(self, p):
        if len(self.points) < 2:
            return
            
        for i, curve_p in list(enumerate(self.points)):
            if p.x == curve_p.x:
                self.points.pop(i)
    
    def calculate_curve(self):
        # Initialize boundary curve points
        if len(self.points) != 0:
            p = self.points[0]
            for i in range(0, p.x):
                self.curve[i] = p.y

            p = self.points[-1]
            for i in range(p.x, 256):
                self.curve[i] = p.y

        # Plot curves
        for i in range(0, len(self.points) - 1): # int i = 0; i < points.size() - 1; i++)
            if i == 0:
                p1 = self.points[0] #points.elementAt( i );
            else:
                p1 = self.points[i - 1]
            
            p2 = self.points[i]
            p3 = self.points[i + 1]

            if i == len(self.points) - 2:
                p4 = self.points[len(self.points) - 2]# points.elementAt( points.size() - 1 );
            else:
                p4 = self.points[i + 2]

            self.plot_curve( p1, p2, p3, p4)

            # ensure that the control points are used exactly.
            for i in range(0, len(self.points)):#( int i = 0; i < points.size(); i++)
                x = self.points[i].x
                y = self.points[i].y
                self.curve[x] = y

    def get4x4list(self):
        return [[0.0,0.0,0.0,0.0],
                [0.0,0.0,0.0,0.0],
                [0.0,0.0,0.0,0.0],
                [0.0,0.0,0.0,0.0]]

    def plot_curve (self, p1, p2, p3, p4):

        geometry = self.get4x4list()
        tmp1 = self.get4x4list()
        tmp2 = self.get4x4list()
        deltas = self.get4x4list()

        N = 1000

        # construct the geometry matrix from the segment
        for i in range(0, 4):#( int i = 0; i < 4; i++)
            geometry[i][2] = 0
            geometry[i][3] = 0
        
        
        # Get points X and Y
        X = self.X
        Y = self.Y
        geometry[0][X] = float(p1.x)
        geometry[1][X] = float(p2.x)
        geometry[2][X] = float(p3.x)
        geometry[3][X] = float(p4.x)

        geometry[0][Y] = float(p1.y)
        geometry[1][Y] = float(p2.y)
        geometry[2][Y] = float(p3.y)
        geometry[3][Y] = float(p4.y)

        # subdivide the curve N times (N = 1000 )
        # N can be adjusted to give a finer or coarser curve
        d = 1.0 / N
        d2 = d * d
        d3 = d * d * d

        # construct a temporary matrix for determining the forward differencing deltas
        tmp2[0][0] = 0.0
        tmp2[0][1] = 0.0
        tmp2[0][2] = 0.0
        tmp2[0][3] = 1.0
        tmp2[1][0] = d3
        tmp2[1][1] = d2
        tmp2[1][2] = d
        tmp2[1][3] = 0.0
        tmp2[2][0] = 6.0 * d3
        tmp2[2][1] = 2.0 * d2
        tmp2[2][2] = 0.0
        tmp2[2][3] = 0.0
        tmp2[3][0] = 6.0 * d3
        tmp2[3][1] = 0.0
        tmp2[3][2] = 0.0
        tmp2[3][3] = 0.0


        # compose the basis and geometry matrices
        self.curves_CR_compose(CR_BASIS, geometry, tmp1)

        # compose the above results to get the deltas matrix
        self.curves_CR_compose(tmp2, tmp1, deltas)

        # extract the x deltas
        x = deltas[0][0]
        dx = deltas[1][0]
        dx2 = deltas[2][0]
        dx3 = deltas[3][0]

        # extract the y deltas
        y = deltas[0][1]
        dy = deltas[1][1]
        dy2 = deltas[2][1]
        dy3 = deltas[3][1]

        lastx = clamp(round(x))
        lasty = clamp(round(y))

        self.curve[lastx] = lasty

        # Loop over the curve and build LUT
        for i in range(0, N):
            # increment the x values
            x += dx
            dx += dx2
            dx2 += dx3
            
            # increment the y values
            y += dy
            dy += dy2
            dy2 += dy3

            newx = clamp(round( x ))
            newy = clamp(round( y ))

            # if this point is different than the last one...then draw it
            if (( lastx != newx ) or ( lasty != newy)):
                self.curve[ newx ] = newy

            lastx = newx;
            lasty = newy;

    # Fills ab using a and b 
    def curves_CR_compose(self, a, b, ab):
        for i in range(0, 4):
            for j in range(0, 4):
                ab[i][j] = (a[i][0] * b[0][j] + \
                a[i][1] * b[1][j] + \
                a[i][2] * b[2][j] + \
                a[i][3] * b[3][j])


class CatmullRomFilter:
    
    def __init__(self, editable_properties):
        # These properties hold the values that are writtenout to MLT to do the filtering
        self.r_table_prop = filter(lambda ep: ep.name == "R_table", editable_properties)[0]
        self.g_table_prop = filter(lambda ep: ep.name == "G_table", editable_properties)[0]
        self.b_table_prop = filter(lambda ep: ep.name == "B_table", editable_properties)[0]
        
        # These properties hold points lists which define cr curves. They are persistent but are not 
        # written oput to MLT
        self.r_points_prop = filter(lambda ep: ep.name == "r_curve", editable_properties)[0]
        self.g_points_prop = filter(lambda ep: ep.name == "g_curve", editable_properties)[0]
        self.b_points_prop = filter(lambda ep: ep.name == "b_curve", editable_properties)[0]
        self.value_points_prop = filter(lambda ep: ep.name == "value_curve", editable_properties)[0]

        # These are objects that generate lut tables from points lists
        self.r_cr_curve = CRCurve()
        self.g_cr_curve = CRCurve()
        self.b_cr_curve = CRCurve()
        self.value_cr_curve = CRCurve()

    def update_table_property_values(self):
        gamma = self.value_cr_curve.curve

        r_table = self.apply_gamma_to_channel(gamma, self.r_cr_curve.curve)
        g_table = self.apply_gamma_to_channel(gamma, self.g_cr_curve.curve)
        b_table = self.apply_gamma_to_channel(gamma, self.b_cr_curve.curve)
        
        self.r_table_prop.write_out_table(r_table)
        #self.g_table_prop.write_out_table(g_table)
        #self.b_table_prop.write_out_table(b_table)
        
    def apply_gamma_to_channel(self, gamma, channel_pregamma):
        lut = []
        # Value for table index 0
        try:
            val = gamma[0] * (gamma[0] / channel_pregamma[0])
        except:
            val = gamma[0]
        lut.append(clamp(round(val)))

        # Value for table index 1 - 255
        for i in range(1, 256):
            gmul = float(gamma[i]) / float(LINEAR_LUT_256[i])
            val = gmul * float(channel_pregamma[i])
            lut.append(clamp(round(val)))
        
        return lut

    
def clamp(val):
    if val > 255:
        return 255
    if val < 0:
        return 0

    return int(val)
