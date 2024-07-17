import math, random
from panda3d.core import *

def Cloud(radius = 1):
    '''Spawn drones in a "random" condensed area'''

    x = 2 * random.random() - 1
    y = 2 * random.random() - 1
    z = 2 * random.random() - 1

    unitVec = Vec3(x, y, z)
    unitVec.normalize()

    return unitVec * radius

def BaseballSeams(step, numSeams, B, F = 1):
    '''Spawn drones in a baseball seam pattern'''

    time = step / float(numSeams) * 2 * math.pi
    F4 = 0
    R = 1

    xxx = math.cos(time) - B * math.cos(3 * time)
    yyy = math.sin(time) + B * math.sin(3 * time)
    zzz = F * math.cos(2 * time) + F4 * math.cos(4 * time)

    rrr = math.sqrt(xxx ** 2 + yyy ** 2 + zzz ** 2)

    x = R * xxx / rrr
    y = R * yyy / rrr
    z = R * zzz / rrr

    return Vec3(x, y, z)

def CircleX(step):
    theta = (step / 60) * 2 * math.pi
    pos = 50.0 * math.cos(theta), 50.0 * math.sin(theta), 0.0
    return Vec3(pos)

def CircleY(step):
    theta = (step / 60) * 2 * math.pi
    pos = 50.0 * math.cos(theta), 0.0, 50.0 * math.sin(theta)
    return Vec3(pos)

def CircleZ(step):
    theta = (step / 60) * 2 * math.pi
    pos = 0.0, 50.0 * math.cos(theta), 50.0 * math.sin(theta)
    return Vec3(pos)