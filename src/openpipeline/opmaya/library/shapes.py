import maya.cmds as mc

def circleShape(name='crnode', radius=1, typeOverride=None):
    '''
    typeOverride args: [float, float, float]
    '''
    # create curve circle
    crv = mc.circle( nr=(0, 1, 0), c=(0, 0, 0), r=radius , n=name)[0]
    # delete history
    mc.delete(crv, ch=True)
    
    mc.setAttr(f"{crv}.overrideEnabled", True)

    if typeOverride:
        # enable and set color RGB override
        mc.setAttr(f"{crv}.overrideRGBColors", True)
        mc.setAttr(f"{crv}.overrideColorRGB", typeOverride[0], typeOverride[1], typeOverride[2])
    else:
        # enable and set default (blue) color Index override
        mc.setAttr(f"{crv}.overrideColor", 6)
    return crv

def customShape(shapeData:dict, shapeLabel='square', radius=1, name='crnode', typeOverride=None, rgb:list|None=None, indexColor=6):
    '''
    typeOverride args: [float, float, float]
    '''
    # create empty group to place every shape node
    crv = mc.group(em=True, n=name)

    # gather the shape dictionary data
    print(shapeData)

    # obtain the squareShape data
    shapeName = shapeData[shapeLabel]
    print(shapeName)

    # get every shape within the shape name data
    # get each shape's control vertex number and position
    cv_nums = shapeName['CV_Numbers']
    cv_pos = shapeName['CV_Positions']
    degrees = shapeName['Degrees']
    forms = shapeName['Form_Index']

    # get the name of each shape and the amount of control vertex numbers it contains
    for shapeNode, numCV in cv_nums.items():
        print(shapeNode)
        print(numCV)
        
        form = forms.get(shapeNode)
        print(form)
        if form==2:
            shp = mc.circle( nr=(0, 1, 0), c=(0, 0, 0), r=1, n=shapeNode)[0]
            for n in range(numCV):
                cv_key = f'{shapeNode}.cv[{n}]'

                points = (cv_pos[cv_key][0]*radius,
                          cv_pos[cv_key][1]*radius, 
                          cv_pos[cv_key][2]*radius)
                mc.xform(cv_key, os=True, t=points)
        else:
            cv_positions=[]
            for n in range(numCV):
                cv_key = f'{shapeNode}.cv[{n}]'

                if cv_key in cv_pos:
                    points = (cv_pos[cv_key][0]*radius, 
                              cv_pos[cv_key][1]*radius, 
                              cv_pos[cv_key][2]*radius)
                    print(points)
                    cv_positions.append(tuple(points))

            degree = degrees.get(shapeNode)
            print(degree)
            print(cv_positions)
            shp = mc.curve(p=cv_positions, n=f'{shapeNode}_shp_grp', d=degree)
        mc.rename(shp, f'{shapeNode}_shp_grp')

    # select and store all the transform groups containing the shape nodes
    grpsToDelete = mc.ls('*_shp_grp')
    for grp in grpsToDelete:
        shapeObj = mc.listRelatives(grp, shapes=True, type='nurbsCurve')[0]
        mc.parent(shapeObj, crv, relative=True, shape=True)
        mc.rename(shapeObj, f'{name}_shp')
        mc.delete(grp)

    # clear selection
    mc.select(clear=True)

    # delete history
    mc.delete(crv, ch=True)

    # if scaleValue <= 0: 
    #     mc.xform(crv, scale=[1,1,1])
    # else:
    #     mc.xform(crv, scale=[scaleValue, scaleValue, scaleValue])
        
    mc.setAttr(f"{crv}.overrideEnabled", True)

    if typeOverride:
        # enable and set color RGB override
        mc.setAttr(f"{crv}.overrideRGBColors", True)
        mc.setAttr(f"{crv}.overrideColorRGB", typeOverride[0], typeOverride[1], typeOverride[2])
    else:
        # enable and set default (blue) color Index override
        mc.setAttr(f"{crv}.overrideColor", 6)

    if rgb:
        # enable and set color RGB override
        mc.setAttr(f"{crv}.overrideRGBColors", True)
        mc.setAttr(f"{crv}.overrideColorRGB", rgb[0], rgb[1], rgb[2])
    else:
        # enable Index override
        mc.setAttr(f"{crv}.overrideColor", indexColor)

    return crv

