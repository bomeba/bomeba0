"""
A collection of common mathematical functions written for high performance with
the help of numpy and numba.
"""
import numpy as np
from math import sin as msin
from math import cos as mcos
from numba import jit



@jit
def dist(p, q):
    """
    Compute distance between two 3D vectors
    p: array
        Cartesian coordinates for one of the vectors
    q: array
        Cartesian coordinates for one of the vectors
    """
    return ((p[0] - q[0])**2 + (p[1] - q[1])**2 + (p[2] - q[2])**2)**0.5


@jit
def dot(p, q):
    """
    Compute dot product between two 3D vectors
    p: array
        Cartesian coordinates for one of the vectors
    q: array
        Cartesian coordinates for one of the vectors
    """
    return p[0] * q[0] + p[1] * q[1] + p[2] * q[2]


@jit
def cross(p, q):
    """
    Compute cross product between two 3D vectors
    p: array
        Cartesian coordinates for one of the vectors
    q: array
        Cartesian coordinates for one of the vectors
    """
    xyz = np.zeros(3)
    xyz[0] = p[1] * q[2] - p[2] * q[1]
    xyz[1] = p[2] * q[0] - p[0] * q[2]
    xyz[2] = p[0] * q[1] - p[1] * q[0]
    return xyz


@jit
def mod(p):
    """
    Compute modulus of 3D vector
    p: array
        Cartesian coordinates
    """
    return (p[0]**2 + p[1]**2 + p[2]**2)**0.5


@jit
def normalize(p):
    """
    Compute a normalized 3D vector
    p: array
        Cartesian coordinates
    """
    return p / mod(p)


@jit
def perp_vector(p, q, r):
    """
    Compute perpendicular vector to (p-q) and (r-q) centered in q.
    """
    v = cross(q - r, q - p)
    return v / mod(v) + q


def get_angle(a, b, c):
    """
    Compute the angle given 3 points
    xyz: array
        Cartesian coordinates
    a-c: int
        atom index for the three points defining the angle
    """

    ba = a - b
    cb = c - b

    ba_mod = mod(ba)
    cb_mod = mod(cb)
    val = dot(ba, cb) / (ba_mod * cb_mod)
    # better fix?
    if val > 1:
        val = 1
    elif val < -1:
        val = -1

    return np.arccos(val)

# this function is the same as get_torsional_array, except that the last one need an xyz-array and
# this one do not.
def get_torsional(a, b, c, d):
    """
    Compute the torsional angle given four points
    a-d: int
        atom index for the four points defining the torsional
   """
    
    # Compute 3 vectors connecting the four points
    ba = b - a
    cb = c - b
    dc = d - c
    
    # Compute the normal vector to each plane
    u_A = cross(ba, cb)
    u_B = cross(cb, dc)

    #Measure the angle between the two normal vectors
    u_A_mod = mod(u_A)
    u_B_mod = mod(u_B)
    val = dot(u_A, u_B) / (u_A_mod * u_B_mod)
    # better fix?
    if val > 1:
        val = 1
    elif val < -1:
        val = -1
    tor_rad = np.arccos(val)
        
    # compute the sign
    sign = dot(u_A, dc)
    if sign > 0:
        return tor_rad
    else:
        return -tor_rad


def get_torsional_array(xyz, a, b, c, d):
    """
    Compute the torsional angle given four points
    xyz: array
        Cartesian coordinates
    a-d: int
        atom index for the four points defining the torsional
   """

    # Compute 3 vectors connecting the four points
    ba = xyz[b] - xyz[a]
    cb = xyz[c] - xyz[b]
    dc = xyz[d] - xyz[c]

    # Compute the normal vector to each plane
    u_A = cross(ba, cb)
    u_B = cross(cb, dc)

    # Measure the angle between the two normal vectors
    u_A_mod = mod(u_A)
    u_B_mod = mod(u_B)
    val = dot(u_A, u_B) / (u_A_mod * u_B_mod)
    # better fix?
    if val > 1:
        val = 1
    elif val < -1:
        val = -1
    tor_rad = np.arccos(val)

    # compute the sign
    sign = dot(u_A, dc)
    if sign > 0:
        return tor_rad
    else:
        return -tor_rad


@jit
def rotation_matrix_3d(u, theta):
    """Return the rotation matrix due to a right hand rotation of theta radians
    around an arbitrary axis/vector u.
    u: array 
        arbitrary axis/vector u
    theta: float
        rotation angle in radians
    """
    x, y, z = normalize(u)
    st = msin(theta)
    ct = mcos(theta)
    mct = 1 - ct

    # filling the matrix by indexing each element is faster (with jit)
    # than writting np.array([[, , ], [, , ], [, , ]])
    R = np.zeros((3, 3))
    R[0, 0] = ct + x * x * mct
    R[0, 1] = y * x * mct - z * st
    R[0, 2] = x * z * mct + y * st
    R[1, 0] = y * x * mct + z * st
    R[1, 1] = ct + y * y * mct
    R[1, 2] = y * z * mct - x * st
    R[2, 0] = x * z * mct - y * st
    R[2, 1] = y * z * mct + x * st
    R[2, 2] = ct + z * z * mct

    return R


@jit
def set_torsional(xyz, i, j, idx_rot, theta_rad):
    """
    rotate a set of coordinates around the i-j axis by theta_rad
    xyz: array
        Cartesian coordinates
    i: int 
        atom i
    j: int 
        atom j
    idx_to_rot: array
        indices of the atoms that will be rotated
    theta_rad: float
        rotation angle in radians
    """
    xyz_s = xyz - xyz[i]
    R = rotation_matrix_3d((xyz_s[j]), theta_rad)
    xyz[:] = xyz_s[:]
    xyz[idx_rot] = xyz_s[idx_rot] @ R
    # TODO return to original position????
    
