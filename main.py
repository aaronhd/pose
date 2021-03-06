
import freenect
from math import sqrt
import numpy as np
from scipy import weave
from time import sleep

clouds = []

#http://personal.ee.surrey.ac.uk/Personal/J.Kilner/python_wiki_files/joe_talk/icp.py
def _get_targets_bad_mem(points_1, points_2):
    """
    Determines the closest point in points_2 for each point in points_1
    
    Parameters:
    points_1, points_2: two sets of points
    
    Returns:
    v_a: vertex assignments, the indices of the nearset point in points_2 for
         each pointin points_1
    delta: the sum of the distances between each point and its target
    """
    # Calculate vertex distances matrices
    d = ((points_1[:,np.newaxis] - points_2[np.newaxis, :]) **2).sum(-1)
    # Find new vertex targets
    v_a = d.argmin(1)
    # Store new squared distances
    delta = d.min(1).sum()
    return v_a, delta

def remove_outliers(x1, x2, v_a, delta):
    """
    """
    x1_new, x2_new = [], []
    for x, y in zip(x1, x2):
        distance = sqrt((y[0] - x[0])**2 + (y[1] - x[1])**2 + (y[1] - x[1])**2)
        print delta
        if (distance > np.average(delta) + 2*sqrt(np.var(delta))) or (distance > np.average(delta) - 2*sqrt(np.var(delta))):
            x1_new.append(x)
            y1_new.append(y)
    return np.array(x1_new), np.array(x2_new)

def get_icp_transform(vertices_1,vertices_2, threshold = 0.005, max_iter = 2):
    """
    Perform Iterative Closest Point optimisation on two sets of vertices
    
    Attempts to determine the rigid transformation which best aligns two meshes
    using the ICP algorithm
    
    Parameters:
    vertices_1, vertices_2: the two sets of vertices to optimise
    threshold: once the distance between the meshes is lower than this
               the optimisation will terminate
    max_iter: the maximum number of iterations to attempt
    
    Returns:
    transform: the rigid transform which best maps vertices_1 on to vertices_2
    vertices: the transformed version of vertices_1
    deltas: the distance between the meshes at the end of each iteration
    
    """

    # Initialise with empty transformation
    transform = np.eye(4)
    # Convert vertices to homogeneous co-ordinates 
    org_x1 = np.hstack((vertices_1,np.ones(len(vertices_1))[:,np.newaxis]))
    x2     = np.hstack((vertices_2,np.ones(len(vertices_2))[:,np.newaxis]))
    # Initialise distance between meshes
    v_a, unused = _get_targets_bad_mem(org_x1,x2)
    # Initialise loop control variables to store squared distance between meshes
    delta = threshold + threshold
    deltas = []
    # Count number of iterations
    actual_iter = 0
    # Loop until the meshes converge
    while delta > threshold:
        # Drop out if we have exceeded maximum iterations
        if max_iter < actual_iter:
            break
        # Transform vertices by best_so_far transform
        x1 = np.dot(org_x1,transform)
        # Find least squares solution to x1 T = x2
        T = np.linalg.lstsq(x1,x2[v_a])[0]
        x1, x2 = remove_outliers(x1, x2, v_a, unused)
        # Calculate vertex distances matrices
        v_a, delta = _get_targets_bad_mem(x1,x2)
        deltas.append(delta)
        # Accumulate the transformation
        transform = np.dot(transform, T)
        # Count the number of actual iterations
        actual_iter += 1
        
    # Return the transformation, the transformed vertices and the squared
    # distances for each iteration 
    return transform, np.dot(org_x1,transform), deltas #[:,:-1]

def RawDepthToMeters(depthValue):
    # http://pille.iwr.uni-heidelberg.de/~kinect01/doc/classdescription.html#kinectcloud-section
    return 1/(depthValue * (-0.0030711016) + 3.3309495161)

def DepthToWorld(x, y, depthValue):

    fx_d = 5.9421434211923247e+02
    fy_d = 5.9104053696870778e+02
    cx_d = 3.3930780975300314e+02
    cy_d = 2.4273913761751615e+02

    depth = RawDepthToMeters(depthValue)
    # http://pille.iwr.uni-heidelberg.de/~kinect01/doc/classdescription.html#kinectcloud-section
    resultZ = float(depth)
    resultX = float((x - cx_d) * resultZ)/fx_d
    resultY = float((y - cy_d) * resultZ)/fy_d
    
    result = [resultX, resultY, resultZ]
    return result

def GenerateCloud():
    global clouds
    cloudCount = len(clouds)
    (depth,_) = freenect.sync_get_depth()
    # Collects 4800 points/frame
    worldCoordinates = np.arange(14400, dtype = np.float64).reshape(60, 80, 3)
    for i in range(0, 480, 8):
        for j in range(0, 640, 8):
            depthValue = depth[i,j]
            if depthValue < 2047:
                # if the depth value is small enough, convert it
                # to depth in meters
                values = DepthToWorld(i, j, depthValue)
                worldCoordinates[i/8, j/8, 0] = values[0]
                worldCoordinates[i/8, j/8, 1] = values[1]
                worldCoordinates[i/8, j/8, 2] = values[2]
            else:
                # otherwise, assign the value to zero
                worldCoordinates[i/8, j/8, 0] = 0
                worldCoordinates[i/8, j/8, 1] = 0
                worldCoordinates[i/8, j/8, 2] = 0
    cloud = []
    for row in worldCoordinates:
        for point in row:
            if str(point) != "[ 0.  0.  0.]":
                cloud.append([point[0],point[1],point[2]])
    if cloudCount < 1:
        clouds.append(cloud)
    else:
        icp = get_icp_transform(cloud, clouds[cloudCount -1])
        print icp[1][:, 0:3]
        clouds.append(icp[1][:, 0:3])
        #clouds.append(np.dot())

print "\n" + "KINECT ONLINE \n"
for i in range(0, 2):
    sleep(1)
    print("Collection " + str(i+1))
    GenerateCloud()
    #if transform.any():
        # rotation = (transform[0:3])[:, 0:3]
        # translation = (transform[-1:])[:, 0:3][0].reshape(3, 1)

with open("output/clouds.asc", "w") as f:
    for cloud in clouds:
        for point in cloud:
            f.write(str(point[0]) + "," + str(point[1]) + "," + str(point[2]) + "\n")