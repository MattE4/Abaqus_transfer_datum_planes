#
# - Script to "copy" datum planes from assembly level to part level
# - Makes it easier to create cuts at specific positions for submodelling or symmetry
#
# - Usage:	- Copy model to create submodel (optional/ as backup)
#			- Remove unneeded instances from assembly (optional)
#			- Create the assembly level datum planes where the cuts should be (if not yet done)
#			- Run Script to get part level datum planes
#			- Go to parts and make cuts as needed
#
#
from abaqus import *
from abaqusConstants import *
from caeModules import *
import random

from abaqus import backwardCompatibility
backwardCompatibility.setValues(reportDeprecated=False)


def run():
	
	###########################################################################################
	# query viewport and model
	vps = session.viewports[session.currentViewportName]
	vpname = vps.name
	modelName = session.sessionState[session.currentViewportName]['modelName']

	m = mdb.models[modelName]
	ra = m.rootAssembly
	inst = ra.instances

	###########################################################################################
	# check instances
	if len(inst.keys()) == 0:
		print 'No instance found'
		return
	
	###########################################################################################
	# query displayed datum planes
	planes = ra.datum
	plane_ids = []
	for pid in planes.keys():
		try:
			planes[pid].normal
			planes[pid].pointOn
			plane_ids.append(pid)
		except:
			pass

	if len(plane_ids) == 0:
		print 'No datum plane found'
		return


	###########################################################################################
	# generate 3 random datum points

	delete_ids = []
	rnumbers = []

	for i in range(9):
		x = random.uniform(-10, 10)
		x = round(x,3)
		rnumbers.append(x)

	p1 = tuple(rnumbers[:3])
	p2 = tuple(rnumbers[3:6])
	p3 = tuple(rnumbers[6:])

	dp1 = ra.DatumPointByCoordinate(coords=p1)
	dp2 = ra.DatumPointByCoordinate(coords=p2)
	dp3 = ra.DatumPointByCoordinate(coords=p3)

	delete_ids.append(dp1.id)
	delete_ids.append(dp2.id)
	delete_ids.append(dp3.id)

	###########################################################################################
	# project datum points to every datum plane and get their coordinates

	projcoords = []
	for pid in plane_ids:
		pp1 = ra.DatumPointByProjOnFace(point=ra.datums[dp1.id], face=ra.datums[pid], isDependent=False)
		c1 = (pp1.xValue, pp1.yValue, pp1.zValue)
		pp2 = ra.DatumPointByProjOnFace(point=ra.datums[dp2.id], face=ra.datums[pid], isDependent=False)
		c2 = (pp2.xValue, pp2.yValue, pp2.zValue)
		pp3 = ra.DatumPointByProjOnFace(point=ra.datums[dp3.id], face=ra.datums[pid], isDependent=False)
		c3 = (pp3.xValue, pp3.yValue, pp3.zValue)

		projcoords.append((c1,c2,c3))
		
		delete_ids.append(pp1.id)
		delete_ids.append(pp2.id)
		delete_ids.append(pp3.id)
	

	###########################################################################################
	# delete random and projected datum points
	
	for f in ra.features.keys():
		if ra.features[f].id in delete_ids:
			del ra.features[f]

	###########################################################################################
	# loop over instances, get their parts, create part csys
	#	loop over all planes (projected points), transform them into part csys, create datum points and new part datum planes

	parts_done = []
	for i in inst.keys():
		
		delete_ids = []	
		part_name = inst[i].partName
		if part_name in parts_done:
			continue

		p = m.parts[part_name]
		pcsys = p.DatumCsysByThreePoints(name='mycsys', coordSysType=CARTESIAN, origin=(0.0, 
			0.0, 0.0), line1=(1.0, 0.0, 0.0), line2=(0.0, 1.0, 0.0), isDependent=False)
		delete_ids.append(pcsys.id)

		ra.regenerate()


		for k in projcoords:
			c1 = inst[i].datums[pcsys.id].globalToLocal(coordinates=(k[0][0], k[0][1], k[0][2]))
			c2 = inst[i].datums[pcsys.id].globalToLocal(coordinates=(k[1][0], k[1][1], k[1][2]))
			c3 = inst[i].datums[pcsys.id].globalToLocal(coordinates=(k[2][0], k[2][1], k[2][2]))

			dp1 = p.DatumPointByCoordinate(coords=c1)
			delete_ids.append(dp1.id)
			dp2 = p.DatumPointByCoordinate(coords=c2)
			delete_ids.append(dp2.id)
			dp3 = p.DatumPointByCoordinate(coords=c3)
			delete_ids.append(dp3.id)
	
			p.DatumPlaneByThreePoints(point1=p.datums[dp1.id], point2=p.datums[dp2.id], point3=p.datums[dp3.id], isDependent=False)
		
		parts_done.append(part_name)
		

		# delete part csys and part datum points
		for f in p.features.keys():
			if p.features[f].id in delete_ids:
				del p.features[f]

	ra.regenerate()


###########################################################################################
if __name__ == "__main__":
	
	run()