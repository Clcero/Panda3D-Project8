from panda3d.core import *
from CollideObjectBase import *
from direct.task.Task import TaskManager
from direct.interval.IntervalGlobal import Sequence
import DefensePaths as defensePaths
import random

class Planet(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Planet, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1.15)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName) 
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Drone(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Drone, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 6)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName) 
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

    # How many drones have been spawned.
    droneCount = 0

class Universe(InverseSphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Universe, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 0.9)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName) 
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class SpaceStation(CapsuleCollidableObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(SpaceStation, self).__init__(loader, modelPath, parentNode, nodeName, 300, -200, 500, 300, -200, -1000, 3750) # Capsule size
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName) 
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Missile(SphereCollideObject):
    fireModels = {}
    cNodes = {}
    collisionSolids = {}
    Intervals = {}
    missileCount = 0

    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float = 1.0):
        super(Missile, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1.0)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setPos(posVec)
        Missile.missileCount += 1
        Missile.fireModels[nodeName] = self.modelNode
        Missile.cNodes[nodeName] = self.collisionNode

        Missile.collisionSolids[nodeName] = self.collisionNode.node().getSolid(0) # Retrieve solid for collisionNode
        print('Fire torpedo #' + str(Missile.missileCount))

class Orbiter(SphereCollideObject):
    numOrbits = 0 # Unique names for tasks
    velocity = random.uniform(0.005, 0.02) # Speed of drone
    cloudTimer = 240 # How long for drone to move

    def __init__(self, loader: Loader, taskMgr: TaskManager, modelPath: str, parentNode: NodePath, nodeName: str, scaleVec: Vec3, texPath: str, centralObject: PlacedObject, orbitRadius: float, orbitType: str, staringAt: Vec3):
        super(Orbiter, self,).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.2)
        self.taskMgr = taskMgr
        self.orbitType = orbitType
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.orbitObject = centralObject
        self.orbitRadius = orbitRadius
        self.staringAt = staringAt
        Orbiter.numOrbits += 1 # Unique names
        self.cloudClock = 0
        
        self.taskFlag = "Traveler-" + str(Orbiter.numOrbits)
        taskMgr.add(self.Orbit, self.taskFlag)
    
    def Orbit(self, task):
        if self.orbitType == "MLB":
            positionVec = defensePaths.BaseballSeams(task.time * Orbiter.velocity, self.numOrbits, 2.0)
            self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())
        
        elif self.orbitType == "Cloud":
            if self.cloudClock < Orbiter.cloudTimer:
                self.cloudClock += 1
                
            else:
                self.cloudClock = 0
                positionVec = defensePaths.Cloud()
                self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())
        
        self.modelNode.lookAt(self.staringAt.modelNode)
        return task.cont


class Wanderer(SphereCollideObject):
    numWanderers = 0

    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, modelName: str, scaleVec: Vec3, texPath: str, staringAt: Vec3):
        super(Wanderer, self).__init__(loader, modelPath, parentNode, modelName, Vec3(0, 0, 0), 3.2)

        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.staringAt = staringAt
        Wanderer.numWanderers += 1

        # Unique start positions and names for each drone
        if Wanderer.numWanderers == 1:
            start_position = Vec3(0, 0, 0)
        else:
            start_position = Vec3(100, 100, 100)
        posInterval0 = self.modelNode.posInterval(20, Vec3(300, 6000, 500), startPos=start_position)
        posInterval1 = self.modelNode.posInterval(20, Vec3(700, -2000, 100), startPos=Vec3(300, 6000, 500))
        posInterval2 = self.modelNode.posInterval(20, Vec3(0, -900, -1400), startPos=Vec3(700, -2000, 100))

        sequence_name = f"Traveler{Wanderer.numWanderers}"
        self.travelRoute = Sequence(posInterval0, posInterval1, posInterval2, name=sequence_name)
        self.travelRoute.loop()


