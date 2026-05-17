import bpy
from typing import Literal
from collections.abc import Callable
from mathutils import Vector

# TODO: add descriptions to matcher
# TODO: add "dead end return" bones to matcher (if there is a dead end, select the stated bone) and alongside that start selecting the first child of a bone where the child's name is not a key in the rules dictionary
class Matcher:
    parent: list[str]
    optional: bool
    roll: Literal["YNeg", "ZNeg", "ZPos"] | None
    callback: Callable[[bpy.types.Bone,bpy.types.Context,str], None]
    dead_end_return: str | None
    def __init__(self,*parents):
        self.optional = False
        self.parent = parents
        self.roll = None
        self.callback = None
        self.dead_end_return = None
    def opt(self):
        self.optional = True
        return self
    def par(self,newparent: str):
        self.parent.append(newparent)
        return self
    def yneg(self):
        self.roll = "YNeg"
        return self
    def zneg(self):
        self.roll = "ZNeg"
        return self
    def zpos(self):
        self.roll = "ZPos"
        return self
    def cback(self,newcallback: Callable[[bpy.types.Bone,bpy.types.Context,str], None]):
        self.callback = newcallback
        return self
    def returning_to(self,bonename: str):
        self.dead_end_return = bonename
        return self

rules = {
  "Hips": Matcher().yneg(),
  "Spine": Matcher("Hips").yneg(),
  "Spine1": Matcher("Spine").opt().yneg(),
  "Spine2": Matcher("Spine","Spine1").yneg(),
  "Neck": Matcher("Spine2").yneg(),
  "Head": Matcher("Neck").yneg(),
  "HeadTop_End": Matcher("Head").opt().yneg(),
}

def rule_chain(optional: bool,roll:Literal["YNeg", "ZNeg", "ZPos"] | None,first_parent: str,first_item: str,*chain):
    the_chain = [first_parent,first_item,*chain]
    for i in range(len(the_chain) - 1):
        the_matcher = Matcher(the_chain[i])
        the_matcher.optional = optional
        the_matcher.roll = roll
        the_matcher.dead_end_return = first_parent
        rules[the_chain[i + 1]] = the_matcher

def eye_callback(bone,context,newname):
    bone.tail = bone.head + Vector((0,0,bone.vector.length))

for side in ["Left","Right"]:
    rules[side + "Eye"] = Matcher("Head").yneg().cback(eye_callback)
    rule_chain(False,"ZNeg","Spine2",side + "Shoulder",side + "Arm",side + "ForeArm",side + "Hand")
    for finger in ["Thumb","Index","Middle","Ring","Pinky"]:
        base = side + "Hand" + finger
        rule_chain(True,"ZNeg",side + "Hand",base + "1",base + "2",base + "3",base + "4")
    rule_chain(True,"YNeg","Hips",side + "UpLeg",side + "Leg")
    rule_chain(True,"YPos",side + "Leg",side + "Foot",side + "ToeBase",side + "Toe_End")

def recurse_test(bone):
    b = bone
    if b is None:
        return None
    ks = set(rules.keys())
    while True:
        if b.name in ks:
            return b
        if b.parent is None:
            return None
        b = b.parent
        # May endless loop if bone loops exist, whoops!

def collect_possible_renames(context):
    ab = context.active_bone
    if rules.get(ab.name,None) is not None:
        return [ab.name] # Rename the bone to itself, and do all the other logic too!
    rule_bone = recurse_test(ab)
    eb = context.active_object.data.edit_bones
    return [
      key for key,value in rules.items() if (value.parent == () if rule_bone is None else (rule_bone.name in value.parent and eb.get(key,None) is None))
    ]

def rename_bone(bone,context,newname: str,reparent=False,run_callback=True):
    bone.name = newname
    associated_rule = rules.get(newname,None)
    if reparent and associated_rule is not None:
        if associated_rule.parent is None:
            bone.parent = None
        elif bone.parent is not None:
            new_parent = recurse_test(bone.parent)
            if new_parent != bone and new_parent != bone.parent:
                bone.use_connect = False
                bone.parent = new_parent
    if associated_rule is not None and associated_rule.callback is not None and run_callback:
        associated_rule.callback(bone,context,newname)
    newroll = None
    if associated_rule is not None:
        newroll = associated_rule.roll
    if newroll == "YNeg":
        bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')
    elif newroll == "YPos":
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')
    elif newroll == "ZNeg":
        bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Z')
    elif newroll == "ZPos":
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
    bone.color.palette = "THEME03"
    # TODO: either add the other roll recalculations, or extend the callback system to be able to chain callbacks
    # ALSO: this way of roll recalculation only works if bone is context.active_bone

def enum_callback(auto_rename,context):
    possible_renames = collect_possible_renames(context)
    print("Enum Callback")
    print(possible_renames)
    return [(n,n,"TODO: Add Description") for n in possible_renames]

class AutoRename(bpy.types.Operator):
    """Semi-Auto renaming of a Bone to match Overte Avatar Standards"""
    bl_idname = "armature.overte_auto_rename"
    bl_label = "Overte Auto Rename"
    bl_options = {"REGISTER","UNDO"}
    bl_property = "rename_to"
    rename_to: bpy.props.EnumProperty(items=enum_callback,name="Rename To")
    do_reparent: bpy.props.BoolProperty(name="Reparent Bone")
    run_callback: bpy.props.BoolProperty(name="Run Callback",default=True)
    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_object is not None and context.active_object.type == "ARMATURE" and context.active_object.data.edit_bones is not None

    def invoke(self, context, event):
        ab = context.active_bone
        possible_renames = collect_possible_renames(context)
        print("Possible Renames:")
        print(possible_renames)
        the_len = len(possible_renames)
        if the_len == 0:
            return {'FINISHED'}
        elif the_len == 1:
            self.rename_to = possible_renames[0]
            return self.execute(context)
        else:
            context.window_manager.invoke_search_popup(self)
            return {'INTERFACE'}

    def execute(self, context):
        rename_bone(context.active_bone,context,self.rename_to,self.do_reparent,self.run_callback)
        if len(context.active_bone.children) == 1:
            context.object.data.edit_bones.active = context.active_bone.children[0]
        return {'FINISHED'}

class AutoFlowBone(bpy.types.Operator):
    """Automatic Flow Bone Renaming (Until no more children or fork in children)"""
    bl_idname = "armature.overte_flow_bone_rename"
    bl_label = "Overte Flow Bone Rename"
    bl_options = {"REGISTER","UNDO"}
    bl_property = "chain_name"
    chain_name: bpy.props.StringProperty(name="Chain Name")
    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_object is not None and context.active_object.type == "ARMATURE" and context.active_object.data.edit_bones is not None
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    def execute(self, context):
        eb = context.active_object.data.edit_bones
        base_name = "flow_"+self.chain_name+"_"
        pre_existing = eb.get(base_name + "1",None)
        if pre_existing is not None:
            self.report({"ERROR"},"Already existing chain with name!")
            return {"CANCELLED"}
        del pre_existing
        current_n = 1
        current_bone = context.active_bone
        while current_bone is not None:
            rename_bone(current_bone,context,base_name + str(current_n))
            current_n += 1
            children = current_bone.children
            current_bone = children[0] if len(children) == 1 else None
        return {"FINISHED"}

class OverteAvatarTodoList(bpy.types.Panel):
    bl_idname = "ARMATURE_PT_OverteAvatarTodoList"
    bl_label = "Overte Avatar To-Do List"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    @classmethod
    def poll(cls,context):
        return context.active_object is not None and context.active_object.type == "ARMATURE" and context.active_object.data.edit_bones is not None
    def draw(self,context):
        l = self.layout
        eb = context.active_object.data.edit_bones
        errors = []
        if len(bpy.data.armatures) < 1: # TODO: only measure armatures in current scene
            errors.append("Missing armature")
        elif len(bpy.data.armatures) > 1:
            errors.append("Too manu armatures")
        for mesh in context.active_object.children:
            for modifier in mesh.modifiers:
                if modifier.type != "ARMATURE":
                    errors.append("Mesh \""+mesh.name+"\" has unsupported modifier named \""+modifier.name+"\"")
        required_next = []
        optional_next = []
        required_otherwise = []
        optional_otherwise = []
        for k,v in rules.items():
            bone = eb.get(k,None)
            has_parent_existing = any(eb.get(parent,None) is not None for parent in v.parent)
            is_next = len(v.parent) == 0 or has_parent_existing
            arr_next = optional_next if v.optional else required_next
            arr_otherwise = optional_otherwise if v.optional else required_otherwise
            arr_append = arr_next if is_next else arr_otherwise
            if bone is None:
                arr_append.append(k)
            else:
                match (len(v.parent) == 0,bone.parent is None):
                    case (True,True):
                        pass
                    case (True,False):
                        errors.append("Bone \"" + k + "\" is parented when it should not be")
                    case (False,True):
                        errors.append("Bone \"" + k + "\" is a root bone when it should be parented to any of " + str(v.parent))
                    case (False,False):
                        if bone.parent.name not in v.parent:
                            errors.append("Bone \"" + k + "\" is parented to \"" + bone.parent.name + "\" when it should be parented to any of " + str(v.parent))
        #TODO: for bone in eb: if is_start_of_flow_bone_chain(bone.name): if_flow_bone_chain_malformed_then_append_errors_about_it(eb,bone,errors)
        #Now we start laying out everything
        needs_sep = False
        def layout_section(needs_sep,l,name,arr):
            if len(arr) == 0:
                return needs_sep
            if needs_sep:
                l.separator()
            l.label(text = name + ":")
            for item in arr:
                l.label(text = item)
            return True
        needs_sep = layout_section(needs_sep,l,"Errors",errors)
        needs_sep = layout_section(needs_sep,l,"Required Next",required_next)
        needs_sep = layout_section(needs_sep,l,"Required Otherwise",required_otherwise)
        needs_sep = layout_section(needs_sep,l,"Optional Next",optional_next)
        needs_sep = layout_section(needs_sep,l,"Optional Otherwise",optional_otherwise)
        # TODO: button that recalculates rolls just in case

def menu_func(self,context):
    if self.layout is None:
        return
    l = self.layout
    l.separator()
    l.operator(AutoRename.bl_idname, text="Auto Rename")
    l.operator(AutoRename.bl_idname, text="Auto Rename and Reparent").do_reparent = True
    l.operator(AutoFlowBone.bl_idname, text="Auto Flow Bone")

# TODO: automatically add keymapping. for now, the process simply needs to be documented

(c_register,c_unregister) = bpy.utils.register_classes_factory((AutoRename,AutoFlowBone,OverteAvatarTodoList))

def register():
    c_register()
    bpy.types.VIEW3D_MT_edit_armature.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_edit_armature.remove(menu_func)
    c_unregister()
