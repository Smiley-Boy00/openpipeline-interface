from . import maya_utils as md
from .. import data_utils as dutil
from . import screenshot as ss
import maya.cmds as mc
import importlib
import os

importlib.reload(md)
importlib.reload(ss)

# Ctrl Shape data saver
def save_selected_shape(dataPath, imgPath, customLabel=None, activeCamera=False, currentBG=False):
    '''Stores curve shape data on a json:
    {str(Shape Name):{int(Control Vertices), list(CV Positions)}}
    '''
    crv_selection = mc.ls(sl=True)

    if len(crv_selection)>1:
        mc.warning('You can only save one shape at a time!')
        return

    if crv_selection:
        
        # check the selection contains a NURBSCurve and store the value
        shapeList=mc.listRelatives(crv_selection[0], shapes=True, type='nurbsCurve')

        if shapeList:
            if not os.path.exists(dataPath):
                os.makedirs(dataPath)
                # empty dictionary where all the data will be stored 
                saveData={}

            else:
                saveData=dutil.load_data(dataPath, 'shapes_cv.json')

            ctrlCV = {}
            posCV = {}
            degreeInfo = {}
            formIndex = {}
            # cycle through every single curve in the selection
            for shapeNode in shapeList:
                print(shapeNode)
                # get the degree, spans and form (open, close, periodic) of the shapes
                deg = mc.getAttr(f'{shapeNode}.degree')
                cv = mc.getAttr(f'{shapeNode}.spans')
                form = mc.getAttr(f'{shapeNode}.form')
                num_cvs = deg+cv
                print(form)
                ctrlCV[shapeNode] = num_cvs # save the amount of control vertices contained in each shape node
                formIndex[shapeNode] = form # save form index value (0=open, 1=close, 2=periodic) related to each shape node
                degreeInfo[shapeNode] = deg # save degree data related to each shape node

                
                # cycle through all of the control vertices in the shape node and get object space position
                for i in range(num_cvs):
                    point = f'{shapeNode}.cv[{i}]'
                    print(point)
                    transform = mc.xform(point, query=True, os=True, t=True) 
                    posCV[point] = transform # save the object space transforms (positions)

            if customLabel:
                shapeName = customLabel # save the user specified shape name label
            else:
                shapeName = crv_selection[0] # save the name for the curve shape

            ss.take_screenshot(crv_selection, imgPath, shapeName, activeCamera=activeCamera, currentBG=currentBG)

            shapeData = {}
            setKeys = ['CV_Numbers', 'CV_Positions', 'Form_Index', 'Degrees']
            setValues = [ctrlCV, posCV, formIndex, degreeInfo]
            for item, each in enumerate(setKeys):
                shapeData[each] = setValues[item]
            saveData.update({shapeName:shapeData})
            print(saveData)

            # write data into json
            dutil.save_data(dataPath, 'shapesCV_Data.json', saveData)
            
        else:
            mc.warning('Make sure your selection is a nurbsCurve Shape')

    else:
        mc.warning('No shape selected')
        return