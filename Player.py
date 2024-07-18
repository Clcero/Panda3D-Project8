from CollideObjectBase import SphereCollideObject
from panda3d.core import Loader, NodePath, Vec3, TransparencyAttrib, CollisionHandlerEvent
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
from direct.task.Task import TaskManager
from typing import Callable
from direct.task import Task
from SpaceJamClasses import Missile
from direct.gui.OnscreenImage import OnscreenImage
import re # For string editing
import random

class Spaceship(SphereCollideObject): # Player
    def __init__(self, base, loader: Loader, taskMgr: TaskManager, accept: Callable[[str, Callable], None], modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 10)
        self.taskMgr = taskMgr
        self.accept = accept
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName) 
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.base = base # Pass base when instanced from Showbase
        self.cntExplode = 0
        self.explodeIntervals = {}

        self._SetCollisions()
        self.SetKeyBindings()
        self.EnableHUD()
        self._SetMissiles()
        self.SetParticles()

        self.taskMgr.add(self.CheckIntervals, 'checkMissiles', 34) # Method to run, name for task, and priority

    # All key bindings for ship's movement.
    def SetKeyBindings(self):
        '''Space moves forwards, WASD are turning controls, Q&E move left and right.
           F shoots a single missile, and Shift+F shoot a barrage.'''
        self.accept('space', self.fwdThrust, [1])
        self.accept('space-up', self.fwdThrust, [0])
        self.accept('a', self.LeftTurn, [1])
        self.accept('a-up', self.LeftTurn, [0])
        self.accept('d', self.RightTurn, [1])
        self.accept('d-up', self.RightTurn, [0])
        self.accept('w', self.UpTurn, [1])
        self.accept('w-up', self.UpTurn, [0])
        self.accept('s', self.DownTurn, [1])
        self.accept('s-up', self.DownTurn, [0])
        self.accept('q', self.leftThrust, [1])
        self.accept('q-up', self.leftThrust, [0])
        self.accept('e', self.rightThrust, [1])
        self.accept('e-up', self.rightThrust, [0])
        self.accept('f', self.Fire) # Fire missile
        self.accept('shift-f', self.FireBarrage) # Fire Missile Barrage
    
    def EnableHUD(self):
        '''Sets aiming reticle.'''
        self.Hud = OnscreenImage(image = "./Assets/Hud/Reticle3b.png", pos = Vec3(0, 0, 0), scale = 0.1)
        self.Hud.setTransparency(TransparencyAttrib.MAlpha)
    
    def _SetCollisions(self):
        '''Handles collision setting and debugging.'''
        self.traverser = self.base.cTrav
        self.handler = CollisionHandlerEvent()
        self.handler.addInPattern('into')
        self.accept('into', self.HandleInto)

    # Missiles
    def _SetMissiles(self):
        '''Defines missile parameters.'''
        self.reloadTime = 0.45
        self.missileDistance = 4000
        self.missileBay = 6

    def Fire(self):
        '''Shoot missile if loaded, otherwise reload.'''
        if self.missileBay: # Check if missile in bay
            travRate = self.missileDistance

            aim = self.base.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()

            fireSolution = aim * travRate
            inFront = aim * 150 # Offset to put at front of spaceship

            travVec = fireSolution + self.modelNode.getPos() # Adjust to always follow model node and in front of player
            self.missileBay -= 1
            tag = 'Missile' + str(Missile.missileCount)
            
            posVec = self.modelNode.getPos() + inFront
            currentMissile = Missile(self.base.loader, './Assets/Phaser/phaser.egg', self.base.render, tag, posVec, 2.0) # Instantiate

            # Duration (2.0), Path to take (travVec), Starting position (posVec), Check collisions between frames (Fluid)
            Missile.Intervals[tag] = currentMissile.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1) # fluid = 1 checks in-between intervals
            
            Missile.Intervals[tag].start()

            self.traverser.addCollider(currentMissile.collisionNode, self.handler)
        
        else:
            if not self.taskMgr.hasTaskNamed('reload'):
                self.taskMgr.doMethodLater(0, self._Reload, 'reload') # Doing it 0 seconds later
                return Task.cont
            

    def FireBarrage(self):
        '''Shoot remaining missiles as a barrage, otherwise reload.'''
        if self.missileBay: # Check if missile in bay
            for i in range(self.missileBay):
                travRate = self.missileDistance

                aim = self.base.render.getRelativeVector(self.modelNode, Vec3(0, 1, 0))
                aim.normalize()
                random_offset = Vec3(random.uniform(-22, 22), random.uniform(-5, 5), random.uniform(-22, 22))

                inFront = aim * 150 + random_offset # Offset to put at front of spaceship
                posVec = self.modelNode.getPos() + inFront

                travVec = aim * self.missileDistance

                self.missileBay -= 1
                tag = 'Missile' + str(Missile.missileCount)
                currentMissile = Missile(self.base.loader, './Assets/Phaser/phaser.egg', self.base.render, tag, posVec, 2.0) # Instantiate

                # Duration (2.0), Path to take (travVec), Starting position (posVec), Check collisions between frames (Fluid)
                endPos = posVec + travVec
                Missile.Intervals[tag] = currentMissile.modelNode.posInterval(2.0, endPos, startPos = posVec, fluid = 1) # fluid = 1 checks in-between intervals
                
                Missile.Intervals[tag].start()
                self.traverser.addCollider(currentMissile.collisionNode, self.handler)
            
        else:
            if not self.taskMgr.hasTaskNamed('reload'):
                self.taskMgr.doMethodLater(0, self._Reload, 'reload') # Doing it 0 seconds later
                return Task.cont


    def _Reload(self, task):
        '''Called as part of Fire function, loads missile after reload time has passed.'''
        if task.time > self.reloadTime:
            self.missileBay += 6
            
            if self.missileBay > 6:
                self.missileBay = 6
            if self.missileBay < 0:
                self.missileBay = 0
            return Task.done
        elif task.time <= self.reloadTime:
            return Task.cont

    def CheckIntervals(self, task):
        '''Handles missile node detachment and deletion.'''
        for i in Missile.Intervals:
            if not Missile.Intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()

                del Missile.Intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                break # Memory still used when dictionary objects are deleted, so we break to refactor.

        return Task.cont
    
    def HandleInto(self, entry):
        '''Handles debugging for collisions, and parses for missile collision detection with drones.'''

        fromNode = entry.getFromNodePath().getName()
        intoNode = entry.getIntoNodePath().getName()

        intoPosition = Vec3(entry.getSurfacePoint(self.base.render))

        tempVar = fromNode.split('_')
        shooter = tempVar[0]
        tempVar = intoNode.split('-')
        tempVar = intoNode.split('_')
        victim = tempVar[0]

        pattern = r'[0-9]' # Remove numbers 0 - 9
        strippedString = re.sub(pattern, '', victim) # Arguments are characters we don't want, what we want to replace, string to edit.
        strippedString = strippedString.split('-')[0] # Remove pattern identifier

        if (strippedString == 'Drone'):
            Missile.Intervals[shooter].finish()
            self.DroneDestroy(victim, intoPosition)
        
        elif strippedString == "Planet":
            Missile.Intervals[shooter].finish()
            self.PlanetDestroy(victim)

        elif strippedString == "Space Station":
            Missile.Intervals[shooter].finish()
            self.SpaceStationDestroy(victim)

        else:
            try:
                Missile.Intervals[shooter].finish()
            except KeyError: # This is required to keep the program from crashing, but doesn't fix the problem.
                pass
    
    def DroneDestroy(self, hitID, hitPosition):
        '''Find a drone with hitID, detach its node, then cause a particle explosions at it's position.'''

        nodeID = self.base.render.find(hitID)
        try:
            nodeID.detachNode()
        except AssertionError: # This is required to keep the program from crashing, but doesn't fix the problem.
            pass
        self.explodeNode.setPos(hitPosition)
        self.Explode(hitPosition)
    
    def PlanetDestroy(self, victim: NodePath):
        nodeID = self.base.render.find(victim)

        self.taskMgr.add(self.PlanetShrink, name = "PlanetShrink", extraArgs = [nodeID], appendTask = True)
    
    def SpaceStationDestroy(self, victim: NodePath):
        nodeID = self.base.render.find(victim)

        self.taskMgr.add(self.SpaceStationShrink, name = "SpaceStationShrink", extraArgs = [nodeID], appendTask = True)
    
    def PlanetShrink(self, nodeID: NodePath, task):
        if task.time < 2.0:
            if nodeID.getBounds().getRadius() > 0:
                if nodeID.getScale() < 0:
                    nodeID.detachNode()
                    return task.done
                scaleSubtraction = 5
                nodeID.setScale(nodeID.getScale() - scaleSubtraction)
                
                temp = 30 * random.random()
                nodeID.setH(nodeID.getH() + temp)
                return task.cont
    
    def SpaceStationShrink(self, nodeID: NodePath, task):
        if task.time < 2.0:
            if nodeID.getBounds().getRadius() > 0:
                if nodeID.getScale() < 0:
                    nodeID.detachNode()
                    return task.done
                scaleSubtraction = 0.01
                nodeID.setScale(nodeID.getScale() - scaleSubtraction)
                
                temp = 30 * random.random()
                nodeID.setH(nodeID.getH() + temp)
                return task.cont
    
    def Explode(self, impactPoint):
        '''Handles particle generation and LerpFunc execution.'''
        self.cntExplode += 1
        tag = 'particles-' + str(self.cntExplode)

        self.explodeIntervals[tag] = LerpFunc(self.ExplodeLight, fromData = 0, toData = 1, duration = 2.0, extraArgs = [impactPoint])
        self.explodeIntervals[tag].start()
    
    def ExplodeLight(self, t, explosionPosition):
        '''Helper function for controlling particle explosion activation parameters.'''
        if t == 1.0 and self.explodeEffect:
            self.explodeEffect.disable()
        
        elif t == 0:
            self.explodeEffect.start(self.explodeNode)
    
    def SetParticles(self):
        '''Enables and sets particle effect settings.'''
        self.base.enableParticles()
        self.explodeEffect = ParticleEffect()
        self.explodeEffect.loadConfig("./Assets/ParticleEffects/Explosions/basic_xpld_efx.ptf")
        self.explodeEffect.setScale(20)
        self.explodeNode = self.base.render.attachNewNode('ExplosionEffects')

    # Movement
    def fwdThrust(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyFwdThrust, 'forward-thrust')
        else:
            self.taskMgr.remove('forward-thrust')
    
    def ApplyFwdThrust(self, task):
        rate = 25
        trajectory = self.base.render.getRelativeVector(self.modelNode, Vec3.forward())
        trajectory.normalize()

        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * rate)

        return Task.cont
    
    def leftThrust(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftThrust, 'left-thrust')
        else:
            self.taskMgr.remove('left-thrust')
    
    def ApplyLeftThrust(self, task):
        rate = 25
        trajectory = self.base.render.getRelativeVector(self.modelNode, Vec3.left())
        trajectory.normalize()

        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * rate)

        return Task.cont

    def rightThrust(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightThrust, 'right-thrust')
        else:
            self.taskMgr.remove('right-thrust')
    
    def ApplyRightThrust(self, task):
        rate = 25
        trajectory = self.base.render.getRelativeVector(self.modelNode, Vec3.right())
        trajectory.normalize()

        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * rate)

        return Task.cont
    

    # Keeps player from going upside down
    def constrainPitch(self):
        '''Constrains pitch to straight up or straight down, does not allow
            the player to go upside down.'''
        pitch = self.modelNode.getP()
        if pitch > 89.0:
            self.modelNode.setP(89.0)
        elif pitch < -89.0:
            self.modelNode.setP(-89.0)

    def updateCameraRotation(self, headingChange, pitchChange):
        '''Updates the camera rotation, calls constrainPitch().'''
        self.modelNode.setH(self.modelNode.getH() + headingChange)
        self.modelNode.setP(self.modelNode.getP() + pitchChange)
        self.constrainPitch()

    # Left and Right Turns - Gimbal locks at high pitch values
    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftTurn, 'left-turn')      
        else:
            self.taskMgr.remove('left-turn')

    def ApplyLeftTurn(self, task):
        rate = 1.25
        self.updateCameraRotation(rate, 0)
        return Task.cont

    def RightTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightTurn, 'right-turn')     
        else:
            self.taskMgr.remove('right-turn')

    def ApplyRightTurn(self, task):
        rate = 1.25
        self.updateCameraRotation(-rate, 0)
        return Task.cont

    # Up and Down Turns - Stops at +-89
    def UpTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyUpTurn, 'up-turn')      
        else:
            self.taskMgr.remove('up-turn')

    def ApplyUpTurn(self, task):
        rate = 1.25
        self.updateCameraRotation(0, rate)
        return Task.cont

    def DownTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyDownTurn, 'down-turn')     
        else:
            self.taskMgr.remove('down-turn')

    def ApplyDownTurn(self, task):
        rate = 1.25
        self.updateCameraRotation(0, -rate)
        return Task.cont

