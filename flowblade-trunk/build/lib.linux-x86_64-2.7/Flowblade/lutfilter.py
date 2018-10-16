"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
import copy

CR_BASIS = [[-0.5,  1.5, -1.5,  0.5],
            [ 1.0, -2.5,  2.0, -0.5],
            [-0.5,  0.0,  0.5,  0.0],
            [ 0.0,  1.0,  0.0,  0.0]]

RED = 0
GREEN = 1
BLUE = 2

SHADOWS = 0
MIDTONES = 1
HIGHLIGHTS = 2

LINEAR_LUT_256 = []
for i in range(0, 256):
    LINEAR_LUT_256.append(i)

MULT_TABLE_256 = []
for i in range(0, 256):
    MULT_TABLE_256.append(0.0)

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
        tokens = points_str.split(";")
        for t in tokens:
            x, y = t.split("/")
            point = CurvePoint(int(x), int(y))
            points.append(point)
        self.points = sorted(points, key=lambda point: point.x)
        self.calculate_curve()

    def get_points_string(self):
        l = []
        for i in range(0, len(self.points)):
            p = self.points[i]
            l.append(str(p.x))
            l.append("/")
            l.append(str(p.y))
            l.append(";")
        return ''.join(l).rstrip(";")
        
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
        # written out to MLT
        self.r_points_prop = filter(lambda ep: ep.name == "r_curve", editable_properties)[0]
        self.g_points_prop = filter(lambda ep: ep.name == "g_curve", editable_properties)[0]
        self.b_points_prop = filter(lambda ep: ep.name == "b_curve", editable_properties)[0]
        self.value_points_prop = filter(lambda ep: ep.name == "value_curve", editable_properties)[0]

        # These are objects that generate lut tables from points lists
        self.r_cr_curve = CRCurve()
        self.r_cr_curve.set_points_from_str(self.r_points_prop.value)
        self.g_cr_curve = CRCurve()
        self.g_cr_curve.set_points_from_str(self.g_points_prop.value)
        self.b_cr_curve = CRCurve()
        self.b_cr_curve.set_points_from_str(self.b_points_prop.value)
        self.value_cr_curve = CRCurve()
        self.value_cr_curve.set_points_from_str(self.value_points_prop.value)

    def update_table_property_values(self):
        # R, G, B LUT table are created with input from value gamma curve to all of them
        gamma = self.value_cr_curve.curve

        r_table = self.apply_gamma_to_channel(gamma, self.r_cr_curve.curve)
        g_table = self.apply_gamma_to_channel(gamma, self.g_cr_curve.curve)
        b_table = self.apply_gamma_to_channel(gamma, self.b_cr_curve.curve)
        
        self.r_table_prop.write_out_table(r_table)
        self.g_table_prop.write_out_table(g_table)
        self.b_table_prop.write_out_table(b_table)

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


class ColorGradeBandCorrection:
    
    def __init__(self):
        self.r_mult = 0.0
        self.g_mult = 0.0
        self.b_mult = 0.0
        
        self.mask_curve = CRCurve()

        self.r_mult_table = copy.deepcopy(MULT_TABLE_256)
        self.g_mult_table = copy.deepcopy(MULT_TABLE_256)
        self.b_mult_table = copy.deepcopy(MULT_TABLE_256)

        self.r_correction_look_up = copy.deepcopy(LINEAR_LUT_256)
        self.g_correction_look_up = copy.deepcopy(LINEAR_LUT_256)
        self.b_correction_look_up = copy.deepcopy(LINEAR_LUT_256)

    def set_hue_and_saturation(self, hue, saturation):
        # Convert saved and editor hue, saturation ranges to one used 
        # to generate look-up tables 
        saturation = (saturation - 0.5) * 2.0
        # Negative saturation means addding complementary color
        if saturation < 0.0:
            saturation = abs(saturation)
            hue = hue + 0.5
            if hue > 1.0:
                hue = hue - 1.0
                
        # Get r, g, b multipliers
        r, g, b = get_RGB_for_angle_saturation_and_value(hue * 360, saturation, 0.5)
        self.r_mult = (r - 0.5) / 0.5 
        self.g_mult = (g - 0.5) / 0.5
        self.b_mult = (b - 0.5) / 0.5
        
        #print r, g, b
        #print self.r_mult, self.g_mult, self.b_mult

    def set_mask_points(self, points_str, range_in, range_out):
        self.mask_curve.set_points_from_str(points_str)
        
        # overwrite parts not in range with value 128
        for i in range(0, range_in):
            self.mask_curve.curve[i] = 128

        for i in range(range_out, 256):
            self.mask_curve.curve[i] = 128

        #self.print_table(self.mask_curve.curve)

    def update_correction(self):
        for i in range(0, 256):
            self.r_mult_table[i] = (float(self.mask_curve.curve[i] - 128) / 128.0) * self.r_mult
            self.g_mult_table[i] = (float(self.mask_curve.curve[i] - 128) / 128.0) * self.g_mult
            self.b_mult_table[i] = (float(self.mask_curve.curve[i] - 128) / 128.0) * self.b_mult
        
        #self.print_table(self.r_mult_table)

        CORRECTION_STRENGTH_MULT = 100.0
        for i in range(0, 256):    
            self.r_correction_look_up[i] = int(self.r_mult_table[i] * CORRECTION_STRENGTH_MULT) #- LINEAR_LUT_256[i]
            self.g_correction_look_up[i] = int(self.g_mult_table[i] * CORRECTION_STRENGTH_MULT) #- LINEAR_LUT_256[i]
            self.b_correction_look_up[i] = int(self.b_mult_table[i] * CORRECTION_STRENGTH_MULT) #- LINEAR_LUT_256[i]
        
        #self.print_table(self.r_correction_look_up)
        
    def print_table(self, table):
        for i in range(0, len(table)):
            print str(i) + ":" + str(table[i])


class ColorGradeFilter:
    
    def __init__(self, editable_properties):
        # These properties hold the values that are writtenout to MLT to do the filtering
        self.r_table_prop = filter(lambda ep: ep.name == "R_table", editable_properties)[0]
        self.g_table_prop = filter(lambda ep: ep.name == "G_table", editable_properties)[0]
        self.b_table_prop = filter(lambda ep: ep.name == "B_table", editable_properties)[0]

        self.r_lookup = [0] * 256 
        self.g_lookup = [0] * 256
        self.b_lookup = [0] * 256 
        
        self.shadow_band = ColorGradeBandCorrection()
        self.shadow_band.set_mask_points("0/128;20/180;45/200;128/146;255/128", 0, 255)
        
        self.mid_band = ColorGradeBandCorrection()
        self.mid_band.set_mask_points("0/128;80/155;128/200;170/155;255/128", 0, 255)

        self.hi_band = ColorGradeBandCorrection()
        self.hi_band.set_mask_points("0/128;128/128;220/200;255/128", 0, 255)

    def update_all_corrections(self):
        self.shadow_band.update_correction()   
        self.mid_band.update_correction()
        self.hi_band.update_correction()

    def update_rgb_lookups(self):
        for i in range(0, 256):
            self.r_lookup[i] = clamp(i + self.shadow_band.r_correction_look_up[i] + \
                                         self.mid_band.r_correction_look_up[i] + \
                                         self.hi_band.r_correction_look_up[i])

            self.g_lookup[i] = clamp(i + self.shadow_band.g_correction_look_up[i] + \
                                         self.mid_band.g_correction_look_up[i] + \
                                         self.hi_band.g_correction_look_up[i])

            self.b_lookup[i] = clamp(i + self.shadow_band.b_correction_look_up[i] + \
                                         self.mid_band.b_correction_look_up[i] + \
                                         self.hi_band.b_correction_look_up[i])

    def write_out_tables(self):
        self.r_table_prop.write_out_table(self.r_lookup)
        self.g_table_prop.write_out_table(self.g_lookup)
        self.b_table_prop.write_out_table(self.b_lookup)


def get_RGB_for_angle(angle):
    hsl = get_HSL(angle, 1.0, 0.5)
    return hsl_to_rgb(hsl)

def get_RGB_for_angle_saturation_and_value(angle, saturation, value):
    hsl = get_HSL(angle,saturation, value)
    return hsl_to_rgb(hsl)
    
def get_HSL(h, s, l):
    h  = h / 360.0
    return (h, s, l)

def hsl_to_rgb(hsl):
    h, s, l = hsl
    
    if s == 0.0:
        #  achromatic case
        r = l
        g = l
        b = l

    else:
    
        if l <= 0.5:
            m2 = l * (1.0 + s)
        else:
            m2 = l + s - l * s

        m1 = 2.0 * l - m2

        r = hsl_value( m1, m2, h * 6.0 + 2.0 )
        g = hsl_value( m1, m2, h * 6.0 )
        b = hsl_value( m1, m2, h * 6.0 - 2.0 )
    
    return (r, g, b)

def hsl_value(n1, n2, hue):
    if hue > 6.0:
        hue -= 6.0
    elif hue < 0.0:
        hue += 6.0

    if hue < 1.0:
        val = n1 + (n2 - n1) * hue
    elif hue < 3.0:
        val = n2
    elif hue < 4.0:
        val = n1 + (n2 - n1) * (4.0 - hue)
    else:
        val = n1

    return val
    
def SQR(v):
    return v * v
    
def clamp(val):
    if val > 255:
        return 255
    if val < 0:
        return 0

    return int(val)


"""
class ColorCorrectorFilter:

    SHADOWS_DIST_MULT = 0.75
    MID_DIST_MULT = 125.0
    HI_DIST_MULT = 0.5

    LIFT_CONV = 0.5 / 127.0
    GAIN_CONV = 0.5 / 127.0 
    GAMMA_CONV = 0.5 / 127.0 

    def __init__(self, editable_properties):
        self.r_table_prop = filter(lambda ep: ep.name == "R_table", editable_properties)[0]
        self.g_table_prop = filter(lambda ep: ep.name == "G_table", editable_properties)[0]
        self.b_table_prop = filter(lambda ep: ep.name == "B_table", editable_properties)[0]

        self.r_lookup = [0] * 256 
        self.g_lookup = [0] * 256
        self.b_lookup = [0] * 256 

        self.cyan_red = [0] * 3
        self.magenta_green = [0] * 3
        self.yellow_blue = [0] * 3

        self.highlights_add = [0] * 256
        self.shadows_sub = [0] * 256

        self.midtones_add = [0] * 256
        self.midtones_sub = [0] * 256

        self.shadows_add = [0] * 256
        self.highlights_sub = [0] * 256

        self._fill_add_sub_tables()
        self.create_lookup_tables()

    def _fill_add_sub_tables(self):
        for i in range(0, 256):
            self.highlights_add[i] = 1.075 - 1.0 / (float(i) / 16.0 + 1.0)
            self.shadows_sub[255 - i] = 1.075 - 1.0 / (float(i) / 16.0 + 1.0)

            self.midtones_add[i] = 0.667 * (1.0 - SQR((float(i) - 127.0) / 127.0))
            self.midtones_sub[i] = 0.667 * (1.0 - SQR((float(i) - 127.0) / 127.0))

            self.shadows_add[i] = 0.667 * (1.0 - SQR((float(i) - 127.0) / 127.0))
            self.highlights_sub[i] = 0.667 * (1.0 - SQR((float(i) - 127.0) / 127.0))

    def set_shadows_correction(self, angle, distance):
        r, g, b = get_RGB_for_angle(angle)
        distance = distance * ColorCorrectorFilter.SHADOWS_DIST_MULT

        max_color = RED
        if g >= r and g >= b:
            max_color = GREEN
        if b >= r and b >= g:
            maxColor = BLUE

        val_R = 0.0
        val_G = 0.0
        val_B = 0.0

        dR = 0.0
        dG = 0.0
        dB = 0.0

        if max_color == RED:
            dG = r - g
            dB = r - b

            val_G = -100.0 * distance * dG
            val_B = -100.0 * distance * dB

        if max_color == GREEN:
            dR = g - r
            dB = g - b

            val_B = -100.0 * distance * dB
            val_R = -100.0 * distance * dR

        if max_color == BLUE:
            dR = b - r
            dG = b - g

            val_G = -100.0 * distance * dG;
            val_R = -100.0 * distance * dR;
        
        self.cyan_red[SHADOWS] = val_R
        self.magenta_green[SHADOWS] = val_G
        self.yellow_blue[SHADOWS] = val_B

    def set_midtone_correction(self, angle, distance):
        rng = distance * ColorCorrectorFilter.MID_DIST_MULT #float range = distance * MID_DIST_MULT;
        floor = -(rng / 2)

        r, g, b = get_RGB_for_angle(angle) #GiottoRGB rgb = getRGB( angle );
        val_R = floor + rng * r
        val_G = floor + rng * g
        val_B = floor + rng * b

        self.cyan_red[MIDTONES] = val_R
        self.magenta_green[MIDTONES] = val_G
        self.yellow_blue[MIDTONES] = val_B
        
    def set_high_ligh_correction(self, angle, distance):
        r, g, b = get_RGB_for_angle(angle)
        distance = distance * ColorCorrectorFilter.HI_DIST_MULT

        min_color = RED
        if g <= r and g <= b:
            min_color = GREEN
        if b <= r and b <= g:
            minColor = BLUE

        val_R = 0.0
        val_G = 0.0
        val_B = 0.0

        dR = 0.0
        dG = 0.0
        dB = 0.0

        if min_color == RED:
            dG = g - r
            dB = b - r

            val_G = 100.0 * distance * dG
            val_B = 100.0 * distance * dB
            val_R = 0.0

        if min_color == GREEN:
            dR = r - g
            dB = b - g

            val_G = 0.0
            val_B = 100.0 * distance * dB
            val_R = 100.0 * distance * dR

        if min_color == BLUE:
            dR = r - b
            dG = b - b

            val_G = 100.0 * distance * dG
            val_B = 0
            val_R = 100.0 * distance * dR

        self.cyan_red[HIGHLIGHTS] = val_R
        self.magenta_green[HIGHLIGHTS] = val_G
        self.yellow_blue[HIGHLIGHTS] = val_B

    def create_lookup_tables(self):
        cyan_red_transfer = [[0] * 3 for i in range(256)] # float[3][256];
        magenta_green_transfer = [[0] * 3 for i in range(256)]
        yellow_blue_transfer =  [[0] * 3 for i in range(256)]

        cyan_red_transfer[SHADOWS] = self.shadows_add if self.cyan_red[ SHADOWS ] > 0 else self.shadows_sub           
        cyan_red_transfer[MIDTONES] = self.midtones_add if self.cyan_red[ MIDTONES ] > 0 else self.midtones_sub
        cyan_red_transfer[HIGHLIGHTS] = self.highlights_add if self.cyan_red[ HIGHLIGHTS ] > 0 else self.highlights_sub

        magenta_green_transfer[SHADOWS] = self.shadows_add if self.magenta_green[SHADOWS] > 0 else self.shadows_sub
        magenta_green_transfer[MIDTONES] = self.midtones_add if self.magenta_green[MIDTONES] > 0 else self.midtones_sub
        magenta_green_transfer[HIGHLIGHTS] = self.highlights_add if self.magenta_green[HIGHLIGHTS] > 0 else self.highlights_sub

        yellow_blue_transfer[SHADOWS] = self.shadows_add if self.yellow_blue[SHADOWS] > 0 else self.shadows_sub
        yellow_blue_transfer[MIDTONES] = self.midtones_add if self.yellow_blue[MIDTONES] > 0 else self.midtones_sub
        yellow_blue_transfer[HIGHLIGHTS] = self.highlights_add if self.yellow_blue[HIGHLIGHTS] > 0 else self.highlights_sub

        for i in range(0, 256):
            r_n = i
            g_n = i
            b_n = i

            r_n +=int(self.cyan_red[SHADOWS] * cyan_red_transfer[SHADOWS][r_n])
            r_n = clamp(r_n)
            r_n += int(self.cyan_red[MIDTONES] * cyan_red_transfer[MIDTONES][r_n])
            r_n = clamp(r_n)
            r_n += int(self.cyan_red[HIGHLIGHTS] * cyan_red_transfer[HIGHLIGHTS][r_n])
            r_n = clamp(r_n)

            g_n += int(self.magenta_green[SHADOWS] * magenta_green_transfer[SHADOWS][g_n])
            g_n = clamp(g_n)
            g_n += int(self.magenta_green[MIDTONES] * magenta_green_transfer[MIDTONES][g_n])
            g_n = clamp(g_n)
            g_n += int(self.magenta_green[HIGHLIGHTS] * magenta_green_transfer[HIGHLIGHTS][g_n])
            g_n = clamp(g_n)

            b_n += int(self.yellow_blue[SHADOWS] * yellow_blue_transfer[SHADOWS][b_n])
            b_n = clamp(b_n)
            b_n += int(self.yellow_blue[MIDTONES] * yellow_blue_transfer[MIDTONES][b_n])
            b_n = clamp(b_n)
            b_n += int(self.yellow_blue[HIGHLIGHTS] * yellow_blue_transfer[HIGHLIGHTS][b_n])
            b_n = clamp(b_n)

            self.r_lookup[i] = r_n
            self.g_lookup[i] = g_n
            self.b_lookup[i] = b_n

    def write_out_tables(self):
        self.r_table_prop.write_out_table(self.r_lookup)
        self.g_table_prop.write_out_table(self.g_lookup)
        self.b_table_prop.write_out_table(self.b_lookup)
        
"""
