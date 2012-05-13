

CLOCKWISE = 1
COUNTER_CLOCKWISE = 2

def point_in_convex_polygon(test_point, points, first_point_index):
    # Polygon has to have > 2 points to caontain anything.
    if len(points) < 3:
        return False

    # Get first points direction
    direction = get_points_direction(   points[first_point_index],
                                        points[first_point_index + 1],
                                        points[first_point_index + 2])

    # direction with two points and test point must always be same 
    # if point is inside polygon.
    for i in range(0, len(points) - 1):
        if get_points_direction(points[i], points[ i + 1], test_point) != direction:
            return False

    if get_points_direction(points[-1], points[0], test_point) != direction:
        return False

    return True;

def get_points_direction(p1, p2, p3):
    if points_clockwise(p1, p2, p3): 
        return CLOCKWISE
    else:
        return COUNTER_CLOCKWISE

def points_clockwise(p1, p2, p3):
    p1x, p1y = p1
    p2x, p2y = p2
    p3x, p3y = p3
    
    e1x = p1x - p2x
    e1y = p1y - p2y
    e2x = p3x - p2x
    e2y = p3y - p2y

    if ((e1x * e2y) - (e1y * e2x)) >= 0: 
        return True
    else:
        return False
