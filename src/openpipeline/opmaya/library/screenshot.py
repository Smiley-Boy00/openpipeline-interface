import maya.cmds as mc
import os

def take_screenshot(selectedObj, path, imageName='.jpg', activeCamera=False, currentBG=False):
    '''Does a single frame playblast render with a default camera.
        Currently only works with curve shapes.'''
    
    pathName = os.path.join(path, imageName)
    if not pathName.endswith('.jpg'):
        pathName += '.jpg'

    # duplicate the selection to not affect the original object/s
    select_dup = mc.duplicate(selectedObj)

    # create group
    # parent duplicate to group 
    temp_grp = mc.group(select_dup, name='screenShot_TEMP_GRP')

    # get the bounding box for the selection
    # set size of each axis (X, Y, Z)
    bbox = mc.exactWorldBoundingBox(temp_grp)
    size_x = bbox[3] - bbox[0]
    size_y = bbox[4] - bbox[1]
    size_z = bbox[5] - bbox[2]
    # set the max size from all three axis
    # set how far the camera will be placed from the selection
    max_size = max(size_x, size_y, size_z)
    cam_distance = max_size*1.15

    # create a default/temporary camera
    if not activeCamera:
        # position it in X, Y, Z with a object's max size * 1.25
        shapeCam = mc.camera(name='shapeCam_TEMP', position=(cam_distance,cam_distance,cam_distance), 
                                                    rotation=(-36.5,45,0), focalLength=55, o=False)[0]
    
        mc.lookThru(shapeCam)

    mc.select(temp_grp)

    # set the background color to a light gray
    if not currentBG:
        ogBackground = mc.displayRGBColor('background', query=True)
        ogBackgroundTop = mc.displayRGBColor('backgroundTop', query=True)
        ogBackgroundBot = mc.displayRGBColor('backgroundBottom', query=True)

        mc.displayRGBColor( 'background', 0.403922, 0.403922, 0.403922 )
        mc.displayRGBColor( 'backgroundTop', 0.403922, 0.403922, 0.403922 )
        mc.displayRGBColor( 'backgroundBottom', 0.403922, 0.403922, 0.403922 )

    # get the current active viewport panel
    current_panel = mc.paneLayout('viewPanes', query=True, pane1=True) 
    # do main screenshot logic
    currentFrame = mc.currentTime(query=True)
    # hide every heads up display widget
    mc.modelEditor(current_panel, edit=True, hud=False)
    mc.grid(toggle=False)
    # view only the selected objects
    mc.isolateSelect(current_panel, state=True)
    mc.isolateSelect(current_panel, addSelected=True)
    # enable anti-aliasing in the viewport
    mc.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    # hide all the objects
    # toggle visible only NURBSCurves and CVs
    mc.modelEditor(current_panel, edit=True, allObjects=False)
    mc.modelEditor(current_panel, edit=True, nurbsCurves=True, controlVertices=True)
    mc.select(clear=True)
    mc.playblast(startTime=0, endTime=1, completeFilename=pathName, format="image", compression="jpg", viewer=False, widthHeight=(256,256))
    # set everything back to default 
    mc.currentTime(currentFrame, edit=True)
    mc.modelEditor(current_panel, edit=True, allObjects=True)
    mc.isolateSelect(current_panel, state=False)
    mc.modelEditor(current_panel, edit=True, hud=True)
    mc.grid(toggle=True)
    mc.delete(temp_grp)

    if not activeCamera:
        mc.delete(shapeCam)
        mc.lookThru('persp')
    
    if not currentBG:
        mc.displayRGBColor('background', ogBackground[0], 
                                        ogBackground[1], 
                                        ogBackground[2])
        
        mc.displayRGBColor('backgroundTop', ogBackgroundTop[0], 
                                        ogBackgroundTop[1], 
                                        ogBackgroundTop[2])
        
        mc.displayRGBColor('backgroundBottom', ogBackgroundBot[0], 
                                        ogBackgroundBot[1], 
                                        ogBackgroundBot[2])

