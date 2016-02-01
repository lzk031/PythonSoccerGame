# soccerGame.py
# Zekun Lyu + zlyu + R

from Tkinter import *
from eventBasedAnimationClass import EventBasedAnimationClass
import math
import random
import datetime
import time
# import pygame
##############################################################################
# some global helper functions
##############################################################################

def rgbString(red, green, blue): #from notes
# create color string using rgb value
    return "#%02x%02x%02x" % (red, green, blue)

def dist(p1,p2):
	# take in positions of two points(storing in tuples) and return the
	# distance between theprintm 
	result = (p1[0]-p2[0])**2+(p1[1]-p2[1])**2
	return math.sqrt(result)

def computeAngle(start, end):
	# take in the start and end point, calculate the cosine and sine
	# of the vector from start to end.
	# note: start and end is tuple
	height =  start[1] - end[1]
	width = end[0] - start[0]
	length = math.sqrt(height**2+width**2)
	if length!=0:
		cos, sin = width/length, height/length
		return cos, sin
	else:
		return 0,0

def decomposeSpeed(speed, angle):
	# take in speed and angle, decompose it into x and y directions.
	dx = speed*angle[0]
	dy = -speed*angle[1]
	return dx,dy

def moduleOfVector(v):
	x,y = v 
	return math.sqrt(x**2+y**2)

def dotProduct(v1, v2):
	(x1, y1) = v1
	(x2, y2) = v2
	return x1*x2+y1*y2

def getAngleBetweenTwoVectors(v1, v2):
	angle = math.acos(dotProduct(v1,v2)/moduleOfVector(v1)/moduleOfVector(v2))
	angle = angle/math.pi*180
	return angle

##############################################################################
# basic class definition
##############################################################################

class Team(object):
	def __init__(self, color, half, field):
		self.half = half
		if self.half=='left':
			self.goal = field.rightGoal
		else:
			self.goal = field.leftGoal
		self.color = color
		self.playerList = []
		self.field = field
		self.score = 0
		self.ownBall = None
		self.teamState = None # "attack" "defend"
		self.opponent = None
		self.pChasingBall = set()

		# the player who controls the ball, the one who drive the ball 
		# or the one who will receive the ball once a pass is made
		# when the team doesn't own the ball, this variable will be set None
		self.pControlBall = None
		self.pUnderControl = None
		self.pReceiveBall = None
		self.pColoseToBall = None
		self.loseBallTime = 0
		self.CreatePlayers()


	def createFormation(self):
		# these functin will create a dictionary which store attacking
		# and defending formation for both the left and the right half
		leftSideFormation = dict()
		leftSideFormation['attack'] = [(1,1), (2,2), (0,4), (2,4)]
		leftSideFormation['defend'] = [(0,1), (2,1), (0,2), (2,2)]


		rightSideFormation = dict()
		rightSideFormation['attack'] = [(1,4), (2,3), (0,1), (2,1)]
		rightSideFormation['defend'] = [(0,4), (2,4), (0,3), (2,3)]
		return leftSideFormation, rightSideFormation


	def getCellAxis(self, row, col):
		# take in row an col, calculate the axis of centre of cell
		xstart, ystart = self.field.startx, self.field.starty
		x = xstart+(col+0.5)*self.field.cellWid
		y = ystart+(row+0.5)*self.field.cellHei
		return x,y

	def CreatePlayers(self):
		(color, field) = (self.color, self.field)
		if self.half == "left":
			goalKeeper = GoalKeeper(field.cellWid/5,field.hei/2,
									color,1, self.field, self)

		else:
			goalKeeper = GoalKeeper(field.wid-field.cellWid/5,
									field.hei/2,color,1, self.field, self)
		self.playerList.append(goalKeeper)

		if self.half == "left":
			cellPosition = [(0,1), (2,1), (0,2), (2,2)]
		else:
			cellPosition = [(0,4), (2,4), (0,3), (2,3)]

		count = 2
		for cell in cellPosition:
			(homeX, homeY) = self.getCellAxis(*cell)
			if count==2 or count==3:
				self.playerList.append(Deffender(homeX, homeY, 
										self.color, count, self.field, self))
			else:
				self.playerList.append(Attacker(homeX, homeY, 
										self.color, count, self.field, self))

			count += 1

	def setHomeCell(self, cellPosition):
		# used to set new home cell when change strategy
		count = 2
		for cell in cellPosition:
			(homeX, homeY) = self.getCellAxis(*cell)
			player = self.playerList[count-1]
			player.homeX, player.homeY = homeX, homeY
			count += 1

	def setTeamState(self, state):
		self.teamState = state
		formations = self.createFormation()
		if self.half=='left':
			formation = formations[0]
		else:
			formation = formations[1]
		self.setHomeCell(formation[state])

	def setKickOffFormation(self):
		# this function will be called when a team make a score
		# it will let the opponent kick off
		opponent = self.opponent
		field = self.field
		field.teamShouldKickOff = opponent
		field.waitForKickOff = 150
		self.teamState = 'waitForKickOff'
		opponent.teamState = 'waitForKickOff'
		opponent.setTeamState('defend')
		self.setTeamState('defend')
		self.teamState = 'waitForKickOff'
		opponent.teamState = 'waitForKickOff'
		attacker1, attacker2 = (opponent.playerList[3], opponent.playerList[4])
		middle = self.field.starty+self.field.fieldHei/2
		if self.half=='left':
			attacker1.homeX,attacker1.homeY = \
			(field.startx+30+field.fieldWid/2, middle-50)
			attacker2.homeX,attacker2.homeY = \
			(field.startx+30+field.fieldWid/2, middle+50)
		else:
			attacker1.homeX,attacker1.homeY = \
			(field.startx-30+field.fieldWid/2, middle-50)
			attacker2.homeX,attacker2.homeY = \
			(field.startx-30+field.fieldWid/2, middle+50)
		ball = self.field.ball
		ball.x, ball.y = field.startx+field.fieldWid/2, middle
		ball.speed = 0


	def findPlayerClosestToBall(self):
		veryLargeDist = 1000
		nearestDist = veryLargeDist
		closest = None
		ball = self.field.ball
		for player in self.playerList:
			distance = dist((player.x,player.y),(ball.x, ball.y))
			if distance<nearestDist and isinstance(player, FieldPlayer)\
										and not player.underControl:
				nearestDist = distance
				closest = player
		return closest

	def onTimerFired(self):
		if self.ownBall==False:
			self.loseBallTime+=1
		maxLoseBallTime = 100
		if self.loseBallTime > maxLoseBallTime:
			player = self.findPlayerClosestToBall()
			player.assignedToChaseBall = True

class Player(object):
	# a universal player which is the super class of all other players
	def __init__(self, homeX, homeY, color, num, field, team):
		self.speed = 3
		self.field = field
		self.team = team
		# homeX and homeY is the axes of the center of the home cell
		self.homeX, self.homeY = homeX, homeY
		self.x = homeX
		self.y = homeY
		self.color = color
		self.num = num 
		self.size = 20 # the radius of the player
		self.canvas = field.canvas
		self.catchArea = 20
		self.dx = 0
		self.dy = 0
		# if is under the control of user
		self.underControl = False
		# if the player is controlling the ball
		self.controlBall = False
		#self.avoidSteal = False
		self.ball = None
		self.wait = 0
		self.lastDistToBall = None
		self.waitForPass = 0
		self.justStealTheBall = 0

	def giveUpBall(self):
		# this function is used when a player should give up the ball
		# passing for example
		if self.controlBall:
			self.controlBall = False
			self.team.pControlBall = None
			self.ball.owner = None
			self.ball = None
			self.team.ownBall = False

	def calculatePassSpeed(self, receiver):
		ball = self.field.ball
		t = 20
		distance = dist((self.x, self.y),(receiver.x, receiver.y))
		v = (distance+0.5*t*t*ball.friction)/t
		return v

	def passBall(self, speed, receiver):
		if self.controlBall:
			try:
				receiver.waitForPass = 20
				receiver.catchArea = 50
			except: pass
			self.ball.speed = speed
			self.ball.angle = computeAngle((self.x, self.y),
											(receiver.x, receiver.y))
			self.giveUpBall()
			waitaMoment = 30
			self.wait = waitaMoment

	def returnHome(self):
		distance = dist((self.x, self.y), (self.homeX, self.homeY))
		nearestDistance = 5
		if distance > nearestDistance:
			angle = computeAngle((self.x, self.y), 
									(self.homeX, self.homeY))
			(self.dx, self.dy) = decomposeSpeed(self.speed, angle)
			self.moveItself(self.dx, self.dy)

	def onTimerFired(self):
		self.wait -= 1
		self.wait = max(self.wait, 0)
		self.waitForPass -= 1
		self.waitForPass = max(self.waitForPass, 0)
		if self.justStealTheBall>0: self.justStealTheBall-=1
		#if not self.controlBall:
		#	self.moveItself(self.dx, self.dy)

	def isInLegalPlace(self):
		field = self.field
		x, y = self.x, self.y
		startx, starty = field.startx, field.starty
		fieldWid, fieldHei = field.fieldWid, field.fieldHei
		if x>startx and x<startx+fieldWid and y>starty and y<starty+fieldHei:
			return True
		else:
			return False

	def moveItself(self, dx, dy):
		# move player and its ball
		if self.waitForPass==0:
			self.x += dx
			self.y += dy
			if self.isInLegalPlace():		
				if self.controlBall:
					(self.ball.x, self.ball.y) = (self.x, self.y)
				return True
			else:
				self.x -= dx
				self.y -= dy
				if self.controlBall:
					(self.ball.x, self.ball.y) = (self.x, self.y)
				return False
		else:
			return None

	def catchBall(self):
		ball = self.field.ball
		(x, y) = (self.x, self.y)
		distance = dist((x,y),(ball.x, ball.y))
		if distance<self.catchArea and type(ball.owner)!=GoalKeeper:
			# and (self.lastDistToBall==None or \
							#distance<self.lastDistToBall)
			# when catch a free ball
			if (ball.owner==None or ball.owner.team!=self.team):
				self.catchArea = 20
				self.controlBall = True
				self.assignedToChaseBall=False
				self.ball = ball
				self.team.ownBall=True
				self.team.opponent.ownBall = False
				self.ball.speed = 0
				if self.ball.owner!=None:
					self.justStealTheBall = 30
					self.ball.owner.controlBall = False
					waitaMoment = 50
					self.ball.owner.wait = waitaMoment
					self.ball.owner.ball = None
				self.ball.owner = self
				(ball.x, ball.y) = (self.x, self.y)
				self.team.setTeamState('attack')
				self.team.pControlBall = self
				if self in self.field.controlTeam.playerList:
					self.team.pUnderControl.underControl = False
					self.team.pUnderControl = self
					self.underControl = True
				try:
					if self in self.field.controlTeam2.playerList:
						self.team.pUnderControl.underControl = False
						self.team.pUnderControl = self
						self.underControl = True
				except: pass
				self.team.opponent.setTeamState('defend')
				self.dx, self.dy = 0,0
		self.lastDistToBall = distance

	def findNearestEnemy(self):
		shortest = None
		for opponent in self.team.opponent.playerList:
			distance = dist((self.x,self.y),(opponent.x,opponent.y))
			if shortest==None:
				shortest = distance
				nearest = opponent
			elif shortest>distance:
				shortest = distance
				nearest = opponent
		return nearest

	def findNearstTeamMate(self):
		nearest = None
		minDist = None
		index = self.num
		for teamMate in self.team.playerList:
			if teamMate != self:
				distance = dist((self.x, self.y), (teamMate.x, teamMate.y))
				if nearest==None:
					nearest = teamMate
					minDist = distance
				elif minDist>distance:
					minDist = distance
					nearest = teamMate
		return nearest

	def enemyNearMe(self, nearDist):
		#nearDist = 100(defend), 50(attack)
		for player in self.team.opponent.playerList:
			distance = dist((self.x,self.y), (player.x, player.y))
			if distance<nearDist: 
				return True
		return False	

	def isUpFieldToMe(self, player):
		if self.team.half=='left':
			if player.x>self.x: return True
			else: return False
		else:
			if player.x<self.x: return True
			else: return False

	def findNearstTeamMateUpField(self):
		nearest = None
		minDist = None
		index = self.num
		for teamMate in self.team.playerList:
			if teamMate != self and self.isUpFieldToMe(teamMate):
				distance = dist((self.x, self.y), (teamMate.x, teamMate.y))
				if nearest==None:
					nearest = teamMate
					minDist = distance
				elif minDist>distance:
					minDist = distance
					nearest = teamMate
		return nearest

	def drawItself(self):
		# at the begin, use circle to stand for player
		(x, y, size, width) = (self.x, self.y, self.size, 5)
		hithLightColor = 'yellow' if self.team.half=='left' else 'grey'
		if self.underControl:
			self.canvas.create_oval(x-size-width, y-size-width, x+size+width, 
									y+size+width, fill=hithLightColor, width=0)
		self.canvas.create_oval(x-size, y-size, x+size, y+size,
								 fill=self.color, width=0)
		self.canvas.create_text(x, y, text = str(self.num))

	def oneOverTenChance(self):
		n = random.randint(1,10)
		if n==1: return True
		else: return False
		
class FieldPlayer(Player):

	def __init__(self, homeX, homeY, color, num, field, team):
		super(FieldPlayer, self).__init__(homeX, homeY, color, num, field, team)
		self.justStealTheBall = 0
		self.assignedToChaseBall = False

	def chaseBall(self):
		angle = computeAngle((self.x, self.y), 
								(self.field.ball.x, self.field.ball.y))
		ball = self.field.ball
		nearestDistToKeeper = 100
		distance = dist((ball.x, ball.y),(self.x, self.y))
		if type(ball.owner)==GoalKeeper and distance<nearestDistToKeeper:
			angle = (-angle[0], angle[1])
		(self.dx, self.dy) = decomposeSpeed(self.speed, angle)
		self.moveItself(self.dx, self.dy)

	def enemyNearMe(self, nearDist):
		#nearDist = 100(defend), 50(attack)
		for player in self.team.opponent.playerList:
			distance = dist((self.x,self.y), (player.x, player.y))
			if distance<nearDist: 
				return True
		return False

	def isInHomeCell(self, x, y):
		# take in x and y and check if the ball or a player is in my home cell
		homeArea = 250
		return dist((self.homeX, self.homeY), (x,y))<homeArea


	def isCloseToBall(self):
		ball = self.field.ball
		closeDist = 200
		return dist((self.x, self.y),(ball.x, ball.y))<closeDist


	def doDefend(self):
		ball = self.field.ball
		if self.isInHomeCell(ball.x, ball.y) or self.isCloseToBall():
			if self.wait==0:
				if len(self.team.pChasingBall)<2 or \
						self in self.team.pChasingBall:
					self.chaseBall()
					self.team.pChasingBall.add(self)
		else:
			if self in self.team.pChasingBall:
				self.team.pChasingBall.remove(self)
			self.returnHome()

	def shootBall(self):
		goal = self.team.goal
		self.passBall(20,goal)
		self.team.ownBall=False


	def closeToGoal(self):
		field = self.field
		goalLine = {'left':field.startx+field.fieldWid, 'right':field.startx}
		middle = field.starty + field.fieldHei/2
		if self.team.half=='left':
			if self.x>goalLine['left']-250 and \
			self.x<field.fieldWid+field.startx:
			 return True
			else: return False
		else:
			if self.x<goalLine['right']+250 and self.x>field.startx:
				return True
			else: return False

	def doAttack(self):
		if not self.underControl:
			self.returnHome()

	def onTimerFired(self):
		super(FieldPlayer, self).onTimerFired()
		self.justStealTheBall-=1
		self.justStealTheBall=max(0,self.justStealTheBall)
		if self.team.teamState=='waitForKickOff'and self.field.waitForKickOff>0:
			self.returnHome()
		elif self.assignedToChaseBall:
			self.chaseBall()
		else:
			if not self.controlBall and self.wait==0: self.catchBall()
			if not self.underControl and self.wait==0:
				if self.team.teamState=='defend':
					self.doDefend()
				elif self.team.teamState=='attack':
					self.doAttack()	

class Attacker(FieldPlayer):
	def __init__(self, homeX, homeY, color, num, field, team):
		super(Attacker, self).__init__(homeX, homeY, color, num, field, team)

	def findBestSupportSpot(self):
		# a really simple solution is here, better one coming soon
		field = self.field
		goalLine = {'left':field.startx+field.fieldWid, 'right':field.startx}
		middle = field.starty + field.fieldHei/2
		#middle += random.randint(-200, 200)
		if self.num==4: middle += random.randint(-200,0)
		if self.num==5: middle += random.randint(0, 200)
		if self.team.half == 'left':
			return (goalLine['left']-200,middle)
		else:
			return (goalLine['right']+200, middle)

	def goToBestSupportSpot(self):
		best = self.findBestSupportSpot()
		distance = dist((self.x, self.y), best)
		nearestDist = 5
		if distance>nearestDist:
			angle = computeAngle((self.x, self.y), 
									(best[0], best[1]))
			(self.dx, self.dy) = decomposeSpeed(self.speed, angle)
			self.moveItself(self.dx, self.dy)

	def enemyFaceMe(self):
		shortest = None
		for opponent in self.team.opponent.playerList:
			distance = dist((self.x,self.y),(opponent.x,opponent.y))
			if shortest==None:
				shortest = distance
				nearest = opponent
			elif shortest>distance:
				shortest = distance
				nearest = opponent
		shortestDistToConsid = 50
		if self.isUpFieldToMe(nearest) and shortest<shortestDistToConsid:
			v1=(nearest.x-self.x, self.y-nearest.y)
			if self.team.half=='left':
				v2=(1,0)
				if nearest.y<self.y:
					enemyIsWhere = 'left'
				else:
					enemyIsWhere = 'right'
			else:
				v2=(-1,0)
				if nearest.y<self.y:
					enemyIsWhere = 'right'
				else:
					enemyIsWhere = 'left'
			angle = getAngleBetweenTwoVectors(v1,v2)
			if angle<30:
				return True,enemyIsWhere
			else:
				return False,
		else:
			return False,
	def dribble(self, direction):
		# direction is the direction you wannar move toward
		distUnit = 5
		if direction=='left':
			if self.team.half=='left':
				self.moveItself(distUnit,-distUnit)
			else:
				self.moveItself(-distUnit,distUnit)
		else:
			if self.team.half=='left':
				self.moveItself(distUnit,distUnit)
			else:
				self.moveItself(-distUnit,-distUnit)

	def attackerControlBall(self):
		field = self.field
		distUnit = self.speed
		foward = {"left":(distUnit,0),"right":(-distUnit,0)}
		backward = {"right":(distUnit,0),"left":(-distUnit,0)}
		leftFoward = {"left":(distUnit,-distUnit),"right":(-distUnit,distUnit)}
		rightFoward = {"right":(-distUnit,-distUnit),
						"left":(distUnit,distUnit)}
		nearest = 50
		if not self.enemyNearMe(nearest) or self.justStealTheBall>0:
			dx, dy = foward[self.team.half]	
			goalLine = {'left':field.startx+field.fieldWid,
						 'right':field.startx}
			if self.closeToGoal():
				if abs(self.x-goalLine[self.team.half])<120:
					self.shootBall()
				else:
					if self.oneOverTenChance():
						self.shootBall()
					else:
						self.moveItself(dx, dy) 
			elif self.moveItself(dx, dy) == False:
				# if the player is in near the boundary, just pass the ball
				# to the nearest teammate
				nearestTeammate = self.findNearstTeamMate()
				ballSpeed = self.calculatePassSpeed(nearestTeammate)
				#ballSpeed = 10
				self.passBall(ballSpeed, nearestTeammate)
		else:
			nearest = self.findNearestEnemy()
			distance = dist((self.x, self.y),(nearest.x,nearest.y))
			if distance<20:
				nearest = self.findNearstTeamMateUpField()
				if nearest == None:
					nearest = self.findNearstTeamMate()
				ballSpeed = self.calculatePassSpeed(nearest)
				if dist((self.x,self.y),(nearest.x, nearest.y))<50:
					ballSpeed=0.5
				if self.justStealTheBall==0:
					self.passBall(ballSpeed, nearest)
				else:
					dx, dy = foward[self.team.half]
					self.moveItself(dx, dy) 

			else:
				if self.enemyFaceMe()[0]:
					enemyIsWhere = self.enemyFaceMe()[1]
					if enemyIsWhere=='left':
						self.dribble('right')
					else:
						self.dribble('left')
				else:
					if self.closeToGoal() and self.oneOverTenChance():
						self.shootBall()
					dx, dy = foward[self.team.half]
					self.moveItself(dx, dy) 

	def doAttack(self):
		ball = self.field.ball
		if not self.underControl :
			if not self.controlBall:
				if dist((self.x,self.y),(ball.x, ball.y))<100 and\
						 (ball.owner==None or ball.owner.team!=self.team):
					self.chaseBall()
				else:
					controller = self.team.pControlBall
					if controller != None and \
					dist((controller.x, controller.y),(self.x, self.y))<50: pass
					else:
						self.goToBestSupportSpot()
			else:
				self.attackerControlBall()
			# dribble or pass to a teammate


class Deffender(FieldPlayer):
	def __init__(self, homeX, homeY, color, num, field, team):
		super(Deffender, self).__init__(homeX, homeY, color, num, field, team)

	def defenderControlBall(self):
		distUnit = self.speed
		foward = {"left":(distUnit,0),"right":(-distUnit,0)}
		backward = {"right":(distUnit,0),"left":(-distUnit,0)}
		leftFoward = {"left":(distUnit,-distUnit),"right":(-distUnit,distUnit)}
		rightFoward = {"right":(-distUnit,-distUnit),"left":(distUnit,distUnit)}
		nearest = 100
		if not self.enemyNearMe(nearest) or self.justStealTheBall>0:
			dx, dy = foward[self.team.half]
			if self.closeToGoal() and self.oneOverTenChance(): self.shootBall()
			elif self.moveItself(dx, dy)==False:
				# if the player is in near the boundary, just pass the ball
				# to the nearest teammate
				nearestTeammate = self.findNearstTeamMate()
				ballSpeed = self.calculatePassSpeed(nearestTeammate)
				#ballSpeed = 10
				self.passBall(ballSpeed, nearestTeammate)
		else:
			nearest = self.findNearstTeamMateUpField()
			if nearest == None:
				nearest = self.findNearstTeamMate()
			#ballSpeed = 10
			ballSpeed = self.calculatePassSpeed(nearest)
			self.passBall(ballSpeed, nearest)

	def doAttack(self):
		ball = self.field.ball
		if not self.underControl :
			if not self.controlBall:
				if dist((self.x,self.y),(ball.x, ball.y))<100:
					self.chaseBall()
				else:
					self.returnHome()
			else:
				self.defenderControlBall()

class GoalKeeper(Player):
	def __init__(self, homeX, homeY, color, num, field, team):
		super(GoalKeeper, self).__init__(homeX, homeY, color, num, field, team)
		self.ballTooFast = 20

	def findMyPosition(self):
		field = self.field
		middle = field.starty+field.fieldHei/2
		if self.team.half=='left':
			self.homeX = field.startx+50
			cx, cy = field.startx-75, middle
		else:
			self.homeX = field.startx+field.fieldWid-50
			cx, cy = field.startx+field.fieldWid+75, middle
		angle = computeAngle((cx, cy), (field.ball.x,field.ball.y))
		self.homeY = cy+angle[1]/angle[0]*(cx-self.homeX)
		if self.homeY>middle+75: self.homeY = middle+75
		if self.homeY<middle-75: self.homeY = middle-75

	def makeSave(self): 
		ball = self.field.ball
		(x, y) = (self.x, self.y)
		distance = dist((x,y),(ball.x, ball.y))
		if distance<self.catchArea:
			if (ball.owner==None or ball.owner.team!=self.team) and \
					ball.speed<self.ballTooFast and\
					random.random()>ball.speed/2/self.ballTooFast:
				self.wait = random.randint(20,40)
				self.catchArea = 20
				self.controlBall = True
				#self.assignedToChaseBall=False
				self.ball = ball
				self.team.ownBall=True
				self.team.opponent.ownBall = False
				self.ball.speed = 0
				if self.ball.owner!=None:
					self.ball.owner.controlBall = False
					waitaMoment = 50
					self.ball.owner.wait = waitaMoment
					self.ball.owner.ball = None
				self.ball.owner = self
				(ball.x, ball.y) = (self.x, self.y)
				self.team.setTeamState('attack')
				self.team.pControlBall = self
				if self in self.field.controlTeam.playerList:
					self.team.pUnderControl.underControl = False
					self.team.pUnderControl = self
					self.underControl = True
				self.team.opponent.setTeamState('defend')
				self.dx, self.dy = 0,0

	def makeGoalKick(self):
		teamMate = self.findNearstTeamMate()
		#ballSpeed = 10
		ballSpeed = self.calculatePassSpeed(teamMate)
		self.passBall(ballSpeed, teamMate)

	def onTimerFired(self):
		super(GoalKeeper, self).onTimerFired()
		if not self.controlBall:
			self.findMyPosition()
			self.returnHome()
			if self.wait==0:
				self.makeSave()
		elif not self.underControl:
			if self.wait>0:
				nearest = self.findNearestEnemy()
				if nearest.y>=self.y:
					self.moveItself(0,-2)
				else:
					self.moveItself(0,2)
			else:
				self.makeGoalKick()

class Ball(object):
	def __init__(self, x, y, field):
		self.x = x
		self.y = y
		self.r = 10
		self.field = field
		self.speed = 0
		self.friction = 0.2
		self.angle = (0,0)
		self.canvas = self.field.canvas
		self.owner = None
		self.img = PhotoImage(file="ball.gif")

	def drawItself(self):
		(r, x, y) = (self.r, self.x, self.y)
		#self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='white', width=0)
		self.canvas.create_image(x,y,image=self.img)

	def moveBall(self):
		self.speed = max(self.speed-self.friction, 0)
		(dx, dy) = decomposeSpeed(self.speed, self.angle)
		self.x += dx
		self.y += dy
		field = self.field
		x, y = self.x, self.y
		startx, starty = field.startx, field.starty
		fieldWid, fieldHei = field.fieldWid, field.fieldHei

	def checkHitBoundary(self):
		field = self.field
		x, y = self.x, self.y
		startx, starty = field.startx, field.starty
		fieldWid, fieldHei = field.fieldWid, field.fieldHei
		if x<startx or x>startx+fieldWid:
			self.angle = (-self.angle[0], self.angle[1])
		elif y<starty or y>starty+fieldHei:
			self.angle = (self.angle[0], -self.angle[1])

	def onTimerFired(self):
		self.checkHitBoundary()
		if self.owner == None:
			self.moveBall()

class Goal(object):
	def __init__(self, x, y, length, field, half):
		self.x = x
		self.y = y
		self.length = length #should be 80 here
		self.wait = 0 # used when a goal is made
		self.field = field
		self.half = half

	def checkHit(self):
		ball = self.field.ball
		goalWidth = 10
		if self.half=='left':
			if ball.x<self.x:
				if ball.y<self.y+self.length and ball.y>self.y-self.length:
					self.field.teams['right'].score+=1
					self.field.teams['right'].setKickOffFormation()
					self.wait=30
					self.field.isRecap = True
		else:
			if ball.x>self.x:
				if ball.y<self.y+self.length and ball.y>self.y-self.length:
					self.field.teams['left'].score+=1
					self.field.teams['left'].setKickOffFormation()
					self.wait=30
					self.field.isRecap = True

	def onTimerFired(self):
		self.checkHit()
		self.wait -= 1
		self.wait = max(self.wait, 0)

	def drawGoal(self):
		canvas = self.field.canvas
		(x, y) = self.x, self.y
		length = self.length
		color = 'white'
		if self.wait>0:
			color = 'pink'
		canvas.create_line(x,y-length/2,x,y+length/2,fill=color,width=20)

class GameField(EventBasedAnimationClass):
	def __init__(self, wid, hei):
		(self.wid, self.hei) = (wid, hei)
		super(GameField, self).__init__(wid, hei)


	def checkHitButton(self, mx, my, bx, by, wid=200, hei=50):
		wid/=2
		hei/=2
		rx, ry = mx-bx, my-by
		if rx<wid and rx>-wid and ry<hei and ry>-hei:
			return True
		else:
			return False


	def onMousePressedStartWindow(self, event):
		bx, by = event.x, event.y
		if self.checkHitButton(bx, by, 500, 380):
			self.gameStart=True
			self.initializeSingleGame()
			# pygame.mixer.music.stop()
			# pygame.mixer.music.load('play.mp3')
			# pygame.mixer.music.play()
		elif self.checkHitButton(bx, by, 500, 450):
			self.gameStart=True
			self.initializeDoubleGame()
			# pygame.mixer.music.stop()
			# pygame.mixer.music.load('play.mp3')
			# pygame.mixer.music.play()
		elif self.checkHitButton(bx, by, 500, 520):
			self.isHelpWindow = True
		elif self.checkHitButton(bx, by, 500, 590):
			self.isHighScoreWindow = True

		# check click back to menu button
		if self.isHelpWindow and self.checkHitButton(bx, by, 800, 600):
			self.isHelpWindow = False

		if self.isHighScoreWindow and self.checkHitButton(bx, by, 800, 600):
			self.isHighScoreWindow = False

	def onMousePressed(self, event):
		if not self.gameStart:
			self.onMousePressedStartWindow(event)

	def goalsOnTimerFired(self):
		for goal in [self.leftGoal, self.rightGoal]:
			goal.onTimerFired()

	def teamsOnTimerFired(self):
		for team in [self.team1, self.team2]:
			team.onTimerFired()

	def insertNewScore(self, highScore):
		oldScore = highScore.splitlines()
		title = oldScore[0]
		score = "%d:%d" % (self.team1.score, self.team2.score)
		today = str(datetime.date.today())
		newLine = " "*5 + "%-10s %s\n" % (score,today)
		oldScore = oldScore[1:]
		scoreDifference = self.team1.score - self.team2.score
		inserted = False
		for x in xrange(len(oldScore)):
			line = oldScore[x]
			line = line.strip()
			line = line.split(" ")[0]
			line = line.split(":")
			oldScoreDifference = int(line[0]) - int(line[1])
			if scoreDifference > oldScoreDifference:
				splited = highScore.splitlines()
				splited = splited[0:x+1] + [newLine[0:-1]] + splited[x+1:]
				inserted = True
				break
		if not inserted: 
			return highScore + newLine
		highScore = ""
		for line in splited:
			highScore += line + "\n"
		return highScore


	def endGame(self):
		self.gameStart = False
		# add score to high score history
		highScore = self.readFile()
		score = "%d:%d" % (self.team1.score, self.team2.score)
		today = str(datetime.date.today())
		text = " "*5 + "%-10s %s\n" % (score,today)
		if highScore==None:
			title = " "*5 + "%-10s"%"score" + " date\n"
			self.writeFile(title+text)
		else:
			highScore = self.insertNewScore(highScore)
			self.writeFile(highScore)

	def calculateTime(self):
		totalTime = self.totalTime #sec
		self.timeLeft = time.time()-self.startTime
		self.timeLeft = int(round(self.timeLeft))
		self.timeLeft =  totalTime - self.timeLeft
		if self.timeLeft < 0:
			if not self.isDoubleGame:
				self.endGame()
			self.initAnimation()

	def checkHoldKey(self):
		if self.controlTeam.ownBall and self.pressed['s']:
			if self.p1BallSpeed<=20:
				self.p1BallSpeed+=2
		try:
			if self.controlTeam2.ownBall and self.pressed['n']:
				if self.p2BallSpeed<=20:
					self.p2BallSpeed+=2
		except: pass

	def gameOnTimerFired(self):
		for player in self.team1.playerList:
			player.onTimerFired()
		for player in self.team2.playerList:
			player.onTimerFired()
		self.reactOnKeyPressed()
		#self.ball.moveBall()
		self.ball.onTimerFired()
		self.goalsOnTimerFired()
		self.calculateTime()
		self.checkHoldKey()

	def loadRecapData(self):
		positionData = []
		for player in self.team1.playerList:
			positionData += [(player.x, player.y)]
		for player in self.team2.playerList:
			positionData += [(player.x, player.y)]
		positionData += [(self.ball.x, self.ball.y)]
		if len(self.recapData)<=600:
			self.recapData += [positionData]
		else:
			self.recapData = self.recapData[1:] + [positionData]

	def resetMovingThings(self):
		stepData = self.recapData[0]
		self.recapData = self.recapData[2:]
		count = 0
		for player in self.team1.playerList:
			(player.x, player.y) = stepData[count]
			count+=1
		for player in self.team2.playerList:
			(player.x, player.y) = stepData[count]
			count+=1
		(self.ball.x, self.ball.y) = stepData[count]

	def resetBallToCenter(self):
		ball, startx, starty = self.ball, self.startx, self.starty
		ball.x, ball.y = startx+self.fieldWid/2, starty+self.fieldHei/2

	def onTimerFired(self):
		#self.catchBall()
		if self.gameStart:
			if self.isRecap == False:
				if self.waitForKickOff>0:
					self.waitForKickOff-=1
					if self.waitForKickOff==0:
						self.team1.teamState = 'defend'
						self.team2.teamState = 'attack'
				self.gameOnTimerFired()
				if self.isRecap == False:
					self.loadRecapData()
			else:
				if len(self.recapData)>0:
					self.resetMovingThings()
					self.recapCount += 1
				else:
					self.isRecap = False
					self.resetBallToCenter()


	def switchControlPlayer(self):
		if not self.controlTeam.ownBall:
			nearest = self.controlTeam.findPlayerClosestToBall()
			self.controlTeam.pUnderControl.underControl = False
			self.controlTeam.pUnderControl = nearest
			nearest.underControl = True

	def switchControlPlayer2(self):
		if not self.controlTeam2.ownBall:
			nearest = self.controlTeam2.findPlayerClosestToBall()
			self.controlTeam2.pUnderControl.underControl = False
			self.controlTeam2.pUnderControl = nearest
			nearest.underControl = True


	def controlPMakeAPass(self):
		controller = self.controlTeam.pUnderControl
		players = controller.team.playerList
		valid = [True] * 5
		valid[controller.num-1] = False
		if self.pressed['i']:
			for x in xrange(5):
				if players[x].y>controller.y:
					valid[x] = False
		if self.pressed['k']:
			for x in xrange(5):
				if players[x].y<controller.y:
					valid[x] = False
		if self.pressed['j']:
			for x in xrange(5):
				if players[x].x>controller.x:
					valid[x] = False
		if self.pressed['l']:
			for x in xrange(5):
				if players[x].x<controller.x:
					valid[x] = False
		nearest = None
		shortest = None
		for x in xrange(5):
			if valid[x]:
				distance = dist((controller.x, controller.y),
								(players[x].x, players[x].y))
				if nearest==None:
					nearest = players[x]
					shortest = distance
				elif distance<shortest:
					nearest = players[x]
					shortest = distance
		if nearest == None:
			nearest = controller.findNearstTeamMate()
		controller.passBall(self.p1BallSpeed, nearest)
		self.p1BallSpeed = 0


	def controlP2MakeAPass(self):
		controller = self.controlTeam2.pUnderControl
		players = controller.team.playerList
		valid = [True] * 5
		valid[controller.num-1] = False
		if self.pressed['Up']:
			for x in xrange(5):
				if players[x].y>controller.y:
					valid[x] = False
		if self.pressed['Down']:
			for x in xrange(5):
				if players[x].y<controller.y:
					valid[x] = False
		if self.pressed['Left']:
			for x in xrange(5):
				if players[x].x>controller.x:
					valid[x] = False
		if self.pressed['Right']:
			for x in xrange(5):
				if players[x].x<controller.x:
					valid[x] = False
		nearest = None
		shortest = None
		for x in xrange(5):
			if valid[x]:
				distance = dist((controller.x, controller.y),
								(players[x].x, players[x].y))
				if nearest==None:
					nearest = players[x]
					shortest = distance
				elif distance<shortest:
					nearest = players[x]
					shortest = distance
		if nearest == None:
			nearest = controller.findNearstTeamMate()
		controller.passBall(self.p2BallSpeed, nearest)
		self.p2BallSpeed = 0

	def controlPMakeAShoot(self):
		try:
			self.controlTeam.pUnderControl.shootBall()
		except:
			pass
	def controlP2MakeAShoot(self):
		try:
			self.controlTeam2.pUnderControl.shootBall()
		except:
			pass

	def reactOnKeyPressed(self):
		if self.pressed["i"]:
			self.controlTeam.pUnderControl.moveItself(0,-3)
		if self.pressed["k"]:
			self.controlTeam.pUnderControl.moveItself(0,3)
		if self.pressed["j"]:
			self.controlTeam.pUnderControl.moveItself(-3,0)
		if self.pressed["l"]:
			self.controlTeam.pUnderControl.moveItself(3,0)
		try:
			if self.pressed["Up"]:
				self.controlTeam2.pUnderControl.moveItself(0,-3)
			if self.pressed["Down"]:
				self.controlTeam2.pUnderControl.moveItself(0,3)
			if self.pressed["Left"]:
				self.controlTeam2.pUnderControl.moveItself(-3,0)
			if self.pressed["Right"]:
				self.controlTeam2.pUnderControl.moveItself(3,0)
		except: pass

	def onKeyReleased(self, event):
		if self.gameStart:
			if event.keysym=='s' and self.controlTeam.ownBall:
				self.controlPMakeAPass()
			self.pressed[event.keysym] = False
			try:
				if event.keysym=='n' and self.controlTeam2.ownBall:
					self.controlP2MakeAPass()
				self.pressed[event.keysym] = False
			except:pass

	def onKeyPressed(self, event):
		if event.keysym=='Escape': self.initAnimation()
		if self.gameStart:
			self.pressed[event.keysym] = True
			if not self.controlTeam.ownBall:
				if event.keysym=="s": self.switchControlPlayer()
			else:
				if event.keysym=="s":pass
					#self.controlPMakeAPass()
				if event.keysym=='d':
					self.controlPMakeAShoot()
			try:
				if not self.controlTeam2.ownBall:
					if event.keysym=="n": self.switchControlPlayer2()
				else:
					if event.keysym=='m':
						self.controlP2MakeAShoot()
			except: pass

	def drawField(self):
		(wid, hei) = (self.wid, self.hei)
		light = rgbString(127, 255, 0)
		dark = rgbString(0, 205, 0)
		chartNum = 10
		for col in xrange(chartNum):
			color = light if col%2==0 else dark
			unit = self.wid/chartNum
			self.canvas.create_rectangle(col*unit, 0, (col+1)*unit, 
											self.hei, fill=color, width=0)

	def drawPlayers(self):
		for player in self.team1.playerList:
			player.drawItself()
		for player in self.team2.playerList:
			player.drawItself()

	def drawBall(self):
		self.ball.drawItself()

	def drawGoals(self):
		for goal in [self.leftGoal, self.rightGoal]:
			goal.drawGoal()

	def drawScore(self):
		x, y = self.startx+self.fieldWid/2, 20
		scoreText="left  %d : %d  right" % (self.team1.score, self.team2.score)
		self.canvas.create_text(x, y, text=scoreText, 
								fill='blue', font='ComicSansMS 20 bold')

	def drawTimer(self):
		minute = self.timeLeft/60
		sec = self.timeLeft%60
		timer = "%02d:%02d" % (minute, sec)
		cx, cy = 800, 20
		self.canvas.create_text(cx, cy, text=timer, 
									fill='blue', font='ComicSansMS 20 bold')
	def drawCamera(self):
		cx, cy = self.startx+self.fieldWid/2, self.starty+self.fieldHei/2
		self.canvas.create_image(cx,cy,image=self.recapImage)


	def drawGame(self):
		self.drawField()
		self.drawPlayers()
		self.drawBall()
		self.drawGoals()
		self.drawScore()
		self.drawTimer()
		if self.isRecap and self.recapCount%40<20:
			self.drawCamera()

	def drawButton(self, cx, cy, text, wid=200, hei=50):
		self.canvas.create_rectangle(cx-wid/2, cy-hei/2, cx+wid/2, 
										cy+hei/2, fill='#4876FF', width=0)
		self.canvas.create_text(cx, cy, text=text, font='ComicSansMS 30 bold')


	def drawStartWindow(self):
		self.canvas.create_image(0,0,anchor='nw',image=self.background)
		title = "Soccer Game"
		cx, cy = self.wid/2, 250
		self.canvas.create_text(cx, cy, text=title,fill='gold',
								 font='ComicSansMS 40 bold')
		# draw start game button
		cx, y = self.wid/2, 380
		buttonWidth = 70
		self.drawButton(cx, y, 'Single Game')
		self.drawButton(cx, y+buttonWidth, 'Two Players')
		# draw help screen button
		self.drawButton(cx, y+2*buttonWidth, 'Help Window')
		# draw high score button
		self.drawButton(cx, y+3*buttonWidth, 'High Score')

	def drawHelpWindow(self):
		self.canvas.create_image(0,0,anchor='nw',image=self.background)
		canvas = self.canvas
		tx, ty = self.wid/2, 100
		title = 'Help Window'
		kindOfBlue = '#4876FF'
		canvas.create_text(tx, ty, text=title, 
							fill=kindOfBlue, font='Romes 30 bold')
		text = self.loadInstruction()
		count = 1
		lineHei = 30
		x, y = 380, ty+50
		for line in text.splitlines():
			canvas.create_text(x, y+count*lineHei, fill='red',text=line,
								anchor=W, font='Times 22')
			count += 1
		bx, by = 800, 600
		self.drawButton(bx, by, 'Go Back')

	def drawHighScoreWindow(self):
		canvas = self.canvas
		tx, ty = self.wid/2, 100
		title = 'High Score'
		kindOfBlue = '#4876FF'
		canvas.create_text(tx, ty, text=title, 
							fill=kindOfBlue, font='Romes 30 bold')
		text = self.readFile()
		count = 1
		lineHei = 30
		x, y = 380, ty+50
		if text == None:
			canvas.create_text(self.wid/2, ty+50, text='No Score History!')
		else:
			for line in text.splitlines():
				canvas.create_text(x, y+count*lineHei, text=line,
									anchor=W, font='ComicSansMS 20 bold')
				count += 1
		bx, by = 800, 600
		self.drawButton(bx, by, 'Go Back')

	def redrawAll(self):
		self.canvas.delete(ALL)
		if self.gameStart:
			if (self.gameStart):
				self.drawGame()
		else:
			if self.isHelpWindow:
				self.drawHelpWindow()
			elif self.isHighScoreWindow:
				self.drawHighScoreWindow()
			else:
				self.drawStartWindow()

	def readFile(self):
		# read high score from the file
		# if there is a file, open it and read the highest score
		try:
			with open("soccerGameHighScore.txt","rt") as fin:
				return fin.read()
		# if there is no file, return None
		except:
			return None

	def writeFile(self, text):
		# write the highest score to file
		with open("soccerGameHighScore.txt","wt") as fout:
			fout.write(text)

	def setTeamSpeed(self,team, speed):
		for player in team.playerList:
			player.speed = speed

	def loadInstruction(self):
		return """Player 1 key control:
'i', 'k', 'j', 'l' to move highlight player up, down,
left, right respectively.
when defending, 
press 's' to change control player. 
when attacking, press 's' to pass, 
press 'd' to shoot

Player 2 key control:
press direction keys to move the player,
press 'n' to change control player or pass the balll
press 'm' to shoot 
"""


	def initializeDoubleGame(self):
		self.startTime = time.time() 
		self.timeLeft = 120#sec
		(self.fieldWid, self.fieldHei) = (self.wid, self.hei)
		self.cellWid = self.fieldWid/self.cols
		self.cellHei = self.fieldHei/self.rows
		self.waitForKickOff = 0
		self.leftGoal = Goal(self.startx,self.starty+self.fieldHei/2,150,
								self,'left')
		self.rightGoal = Goal(self.startx+self.fieldWid,
							self.starty+self.fieldHei/2,150,self,'right')
		self.team1 = Team('red', 'left', self)
		self.team2 = Team('lightblue', 'right', self)
		self.team2.teamState = 'defend'
		self.teams = {"left":self.team1,"right":self.team2}	
		self.controlTeam = self.team1 # the team under player's control
		self.controlTeam2 = self.team2
		self.team1.opponent, self.team2.opponent = self.team2, self.team1
		self.ball = Ball(self.wid/2, self.hei/2, self)
		self.teamShouldKickOff = None
		self.p1BallSpeed = 0 # the initial speed of ball when passing or shoot
		self.p2BallSpeed = 0
		self.controlTeam.pUnderControl = self.team1.playerList[3]
		self.controlTeam.pUnderControl.underControl = True
		self.controlTeam2.pUnderControl = self.team2.playerList[3]
		self.controlTeam2.pUnderControl.underControl = True
		self.pressed = {"i":None,"k":None,"j":None,"l":None,"s":None,"d":None, 
						"Up":None,"Down":None,"Left":None,"Right":None,"n":None,
						"m":None} 
		self.isDoubleGame = True


	def initializeSingleGame(self):
		self.startTime = time.time() 
		self.timeLeft = 120#sec
		(self.fieldWid, self.fieldHei) = (self.wid, self.hei)
		self.cellWid = self.fieldWid/self.cols
		self.cellHei = self.fieldHei/self.rows
		self.waitForKickOff = 0
		self.leftGoal = Goal(self.startx,self.starty+self.fieldHei/2,150,self,'left')
		self.rightGoal = Goal(self.startx+self.fieldWid,
							self.starty+self.fieldHei/2,150,self,'right')
		self.team1 = Team('red', 'left', self)
		self.team2 = Team('lightblue', 'right', self)
		self.team2.teamState = 'defend'
		self.teams = {"left":self.team1,"right":self.team2}	
		self.controlTeam = self.team1 # the team under player's control
		self.team1.opponent, self.team2.opponent = self.team2, self.team1
		self.ball = Ball(self.wid/2, self.hei/2, self)
		self.teamShouldKickOff = None
		self.p1BallSpeed = 0 # the initial speed of ball when passing or shoot
		#self.team2.setKickOffFormation()
		#self.friction = 1
		self.setTeamSpeed(self.team2, 3)
		self.controlTeam.pUnderControl = self.team1.playerList[3]
		self.controlTeam.pUnderControl.underControl = True

	def initAnimation(self):
		# seperate field into several parts
		# size data
		(self.rows, self.cols) = (3, 6)
		self.startx = 0
		self.starty = 0
		self.gameStart = False # for test
		self.isHelpWindow = False
		self.isHighScoreWindow = False
		self.isDoubleGame = False
		self.AILevel = 'freshmen'
		self.AISpeed = {'freshMen':3,'master':4,'elite':5}
		self.pressed = {"i":None,"k":None,"j":None,"l":None,"s":None,"d":None} 
		# store key pressed condition
		self.background = PhotoImage(file="background.gif")
		self.recapImage = PhotoImage(file="recap.gif")
		self.totalTime = 120
		self.recapData = [] # store position information
		self.isRecap = False
		self.recapCount = 0
		# pygame.mixer.init()
		# pygame.mixer.music.load('menu.mp3')
		# pygame.mixer.music.play()


##############################################################################
# test and run
##############################################################################
GameField(1000, 700).run()


