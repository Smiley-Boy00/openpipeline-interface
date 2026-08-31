import maya.cmds as mc

WINDOW_ID="creativeMatch01"

class creativeMatch:
    def __init__(self):
        
        self.fk_controls={"arm":["_shoulder_fk_ctrl", "_elbow_fk_ctrl", "_wrist_fk_ctrl"],
                          "leg":["_hip_fk_ctrl", "_knee_fk_ctrl", "_ankle_fk_ctrl", "_ball_fk_ctrl"]}
        
        self.ik_controls={"arm":["_elbow_ik_ctrl", "_wrist_ik_ctrl"],
                          "leg":["_knee_ik_ctrl", "_foot_ik_ctrl"]}

        self.fk_ctrl=None
        self.ik_ctrl=None
        
        if mc.window(WINDOW_ID, exists=True):
            mc.deleteUI(WINDOW_ID, window=True)

        self.mainWindow=mc.window(WINDOW_ID, title="creativeMatch", widthHeight=(300,200))
        
        self.mainLayout=mc.formLayout(self.mainWindow)

        leftIKArmButton=mc.button(label="Match IK Left Arm", command=self.match)
        rightIKArmButton=mc.button(label="Match IK Right Arm", command=lambda args:self.match(side='right'))

        leftFKArmButton=mc.button(label="Match FK Left Arm", command=lambda args:self.match(match='fk'))
        rightFKArmButton=mc.button(label="Match FK Right Arm", command=lambda args:self.match(side='right'))

        mc.formLayout(self.mainLayout, edit=True, attachForm=[[leftFKArmButton, "top", 10], [leftFKArmButton, "left", 5],
                                                              [rightFKArmButton, "top", 10], [rightFKArmButton, "left", 5],
                                                              [leftIKArmButton, "top", 10], [leftIKArmButton, "left", 5],
                                                              [rightIKArmButton, "top", 10], [rightIKArmButton, "left", 5]],
                                                attachControl=[[leftFKArmButton, "top", 10, leftIKArmButton],
                                                               [rightFKArmButton, "top", 10, rightIKArmButton],
                                                               [rightIKArmButton, "left", 10, leftIKArmButton],
                                                               [rightFKArmButton, "left", 10, leftFKArmButton]])
        
        mc.showWindow()
    
    def match(self, *args, match:str="ik", limb:str="arm", side:str="left"):

        if match == 'ik':
            controlsToMatch=[side+ctrl for ctrl in self.ik_controls.get(limb)]

            mc.setAttr(f"{side}_{limb}_settings_ctrl.IK", 0)
            for ctrl in controlsToMatch:
                if mc.objExists(ctrl):
                    if "elbow" in ctrl or "knee" in ctrl:
                        match_node=ctrl.replace("ik_ctrl", "loc")
                    else:
                        match_node=ctrl.replace("ik_ctrl", "jnt")
                    mc.matchTransform(ctrl, match_node)
            mc.setAttr(f"{side}_{limb}_settings_ctrl.IK", 1)

        elif match == 'fk':
            controlsToMatch=[side+ctrl for ctrl in self.fk_controls.get(limb)]

            mc.setAttr(f"{side}_{limb}_settings_ctrl.IK", 1)
            for ctrl in controlsToMatch:
                if mc.objExists(ctrl):
                    jnt_match=ctrl.replace("fk_ctrl", "jnt")
                    mc.matchTransform(ctrl, jnt_match)
            mc.setAttr(f"{side}_{limb}_settings_ctrl.IK", 0)

    