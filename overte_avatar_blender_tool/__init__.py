import bpy
from typing import Literal
from collections.abc import Callable
from mathutils import Vector

class Matcher:
    parent: list[str]
    optional: bool
    roll: Literal["YNeg", "YPos", "ZNeg", "ZPos"] | None
    callback: Callable[[bpy.types.Bone,bpy.types.Context,str], None]
    dead_end_return: str | None
    description: str
    def __init__(self,*parents):
        self.optional = False
        self.parent = list(parents)
        self.roll = None
        self.callback = None
        self.dead_end_return = None
        self.description = ""
    def opt(self):
        self.optional = True
        return self
    def par(self,newparent: str):
        self.parent.append(newparent)
        return self
    def yneg(self):
        self.roll = "YNeg"
        return self
    def ypos(self):
        self.roll = "YPos"
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
    def desc(self,text: str):
        self.description = text
        return self

ROLL_AXIS = {
  "YNeg": "GLOBAL_NEG_Y",
  "YPos": "GLOBAL_POS_Y",
  "ZNeg": "GLOBAL_NEG_Z",
  "ZPos": "GLOBAL_POS_Z",
}

rules = {
  "Hips": Matcher().yneg(),
  "Spine": Matcher("Hips").yneg(),
  "Spine1": Matcher("Spine").opt().yneg(),
  "Spine2": Matcher("Spine","Spine1").yneg(),
  "Neck": Matcher("Spine2").yneg(),
  "Head": Matcher("Neck").yneg(),
  "HeadTop_End": Matcher("Head").opt().yneg(),
}

def rule_chain(optional: bool,roll:Literal["YNeg", "YPos", "ZNeg", "ZPos"] | None,first_parent: str,first_item: str,*chain):
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
    rule_chain(False,"YNeg","Hips",side + "UpLeg",side + "Leg")
    rules[side + "Foot"] = Matcher(side + "Leg").ypos().returning_to("Hips")
    rule_chain(True,"YPos",side + "Foot",side + "ToeBase",side + "Toe_End")

DESCRIPTIONS = {
  "Hips": "Root pelvis bone",
  "Spine": "Lower spine, above hips",
  "Spine1": "Optional mid-spine bone",
  "Spine2": "Chest (upper spine)",
  "Neck": "Neck, below the head",
  "Head": "Head",
  "HeadTop_End": "Optional head-top marker bone",
}
for _side in ("Left","Right"):
    DESCRIPTIONS[_side + "Eye"] = f"{_side} eye"
    DESCRIPTIONS[_side + "Shoulder"] = f"{_side} shoulder (clavicle)"
    DESCRIPTIONS[_side + "Arm"] = f"{_side} upper arm"
    DESCRIPTIONS[_side + "ForeArm"] = f"{_side} forearm"
    DESCRIPTIONS[_side + "Hand"] = f"{_side} hand"
    DESCRIPTIONS[_side + "UpLeg"] = f"{_side} upper leg (thigh)"
    DESCRIPTIONS[_side + "Leg"] = f"{_side} lower leg (shin)"
    DESCRIPTIONS[_side + "Foot"] = f"{_side} foot"
    DESCRIPTIONS[_side + "ToeBase"] = f"Optional {_side.lower()} toe base"
    DESCRIPTIONS[_side + "Toe_End"] = f"Optional {_side.lower()} toe tip marker"
    for _finger in ("Thumb","Index","Middle","Ring","Pinky"):
        _b = _side + "Hand" + _finger
        DESCRIPTIONS[_b + "1"] = f"{_side} {_finger.lower()}, base joint"
        DESCRIPTIONS[_b + "2"] = f"{_side} {_finger.lower()}, middle joint"
        DESCRIPTIONS[_b + "3"] = f"{_side} {_finger.lower()}, tip joint"
        DESCRIPTIONS[_b + "4"] = f"{_side} {_finger.lower()}, optional end marker"
del _side, _finger, _b
for _name, _desc in DESCRIPTIONS.items():
    if _name in rules:
        rules[_name].description = _desc
del _name, _desc

def recurse_test(bone):
    b = bone
    if b is None:
        return None
    ks = set(rules.keys())
    for _ in range(256):
        if b.name in ks:
            return b
        if b.parent is None:
            return None
        b = b.parent
    return None

def collect_possible_renames(context):
    ab = context.active_bone
    if rules.get(ab.name,None) is not None:
        return [ab.name] # Rename the bone to itself, and do all the other logic too!
    rule_bone = recurse_test(ab)
    eb = context.active_object.data.edit_bones
    return [
      key for key,value in rules.items() if (not value.parent if rule_bone is None else (rule_bone.name in value.parent and eb.get(key,None) is None))
    ]

def rename_bone(bone,context,newname: str,reparent=False,run_callback=True):
    bone.name = newname
    associated_rule = rules.get(newname,None)
    if reparent and associated_rule is not None:
        if not associated_rule.parent:
            bone.parent = None
        elif bone.parent is not None:
            new_parent = recurse_test(bone.parent)
            if new_parent != bone and new_parent != bone.parent:
                bone.use_connect = False
                bone.parent = new_parent
    if associated_rule is not None and associated_rule.callback is not None and run_callback:
        associated_rule.callback(bone,context,newname)
    newroll = associated_rule.roll if associated_rule is not None else None
    if newroll is not None:
        # calculate_roll operates on the active bone, so make sure it's this one
        context.active_object.data.edit_bones.active = bone
        bpy.ops.armature.calculate_roll(type=ROLL_AXIS[newroll])
    bone.color.palette = "THEME03"

def enum_callback(auto_rename,context):
    possible_renames = collect_possible_renames(context)
    return [(n,n,rules[n].description or f"Rename to {n}") for n in possible_renames]

def next_active_after_rename(bone, edit_bones):
    """Pick the bone to make active after a rename, mirroring the speedrun flow.

    Prefers children whose names are not already a known rule key (i.e. not
    yet renamed); on a dead end, follows the rule's dead_end_return.
    """
    fresh_children = [c for c in bone.children if c.name not in rules]
    if len(fresh_children) == 1:
        return fresh_children[0]
    if not fresh_children:
        rule = rules.get(bone.name)
        if rule is not None and rule.dead_end_return:
            return edit_bones.get(rule.dead_end_return)
    return None

def axis_side(x, eps=1e-6):
    """Return 'left', 'right', or 'center' for an X coordinate.

    Blender's convention is +X = character's left side when facing the camera.
    """
    if x > eps:
        return "left"
    if x < -eps:
        return "right"
    return "center"

TOE_SUFFIXES = ("ToeBase","Toe_End")

def is_toe_bone(name):
    return any(name.endswith(s) for s in TOE_SUFFIXES)

def effective_optional(rule, name, toes_required):
    if rule.optional and toes_required and is_toe_bone(name):
        return False
    return rule.optional

def is_flow_chain_root(name):
    return name.startswith("flow_") and name.endswith("_1")

def validate_flow_chains(edit_bones):
    """Return error strings for any malformed flow_*_N chain in edit_bones.

    Accepts anything iterable that yields bones and supports .get(name).
    """
    errors = []
    for bone in edit_bones:
        if not is_flow_chain_root(bone.name):
            continue
        prefix = bone.name[:-1]
        n = 2
        while True:
            current_name = f"{prefix}{n}"
            current = edit_bones.get(current_name)
            if current is None:
                break
            expected_parent = f"{prefix}{n - 1}"
            if current.parent is None or current.parent.name != expected_parent:
                errors.append(f"Flow bone \"{current_name}\" is not parented to \"{expected_parent}\"")
            n += 1
            if n > 256:
                errors.append(f"Flow chain \"{prefix}\" exceeded the 256-link limit")
                break
    return errors

def classify_bones(edit_bones, toes_required=False):
    """Pure classification of the rules table against an armature's edit_bones.

    Returns (errors, required_next, required_otherwise, optional_next, optional_otherwise).
    """
    errors = []
    required_next = []
    optional_next = []
    required_otherwise = []
    optional_otherwise = []
    for k, v in rules.items():
        bone = edit_bones.get(k, None)
        has_parent_existing = any(edit_bones.get(p, None) is not None for p in v.parent)
        is_next = len(v.parent) == 0 or has_parent_existing
        optional = effective_optional(v, k, toes_required)
        arr_next = optional_next if optional else required_next
        arr_otherwise = optional_otherwise if optional else required_otherwise
        arr_append = arr_next if is_next else arr_otherwise
        if bone is None:
            arr_append.append(k)
            continue
        if len(v.parent) == 0:
            if bone.parent is not None:
                errors.append(f"Bone \"{k}\" is parented when it should not be")
        else:
            if bone.parent is None:
                errors.append(f"Bone \"{k}\" is a root bone when it should be parented to any of {v.parent}")
            elif bone.parent.name not in v.parent:
                errors.append(f"Bone \"{k}\" is parented to \"{bone.parent.name}\" when it should be parented to any of {v.parent}")
    return errors, required_next, required_otherwise, optional_next, optional_otherwise

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
        bone = context.active_bone
        rename_bone(bone,context,self.rename_to,self.do_reparent,self.run_callback)
        eb = context.object.data.edit_bones
        next_active = next_active_after_rename(bone,eb)
        if next_active is not None:
            eb.active = next_active
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

class RecalculateAllRolls(bpy.types.Operator):
    """Recalculate roll on every armature bone whose name matches an Overte rule"""
    bl_idname = "armature.overte_recalculate_all_rolls"
    bl_label = "Recalculate All Rolls"
    bl_options = {"REGISTER","UNDO"}
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "ARMATURE" and context.active_object.data.edit_bones is not None
    def execute(self, context):
        eb = context.active_object.data.edit_bones
        count = 0
        for name, rule in rules.items():
            if rule.roll is None:
                continue
            bone = eb.get(name, None)
            if bone is None:
                continue
            eb.active = bone
            bpy.ops.armature.calculate_roll(type=ROLL_AXIS[rule.roll])
            count += 1
        self.report({"INFO"}, f"Recalculated roll on {count} bone(s)")
        return {"FINISHED"}

class SplitShapeKey(bpy.types.Operator):
    """Split a shape key into left/right halves along the X axis.

    For each vertex of the basis mesh, the side with the wrong sign is reset
    to its basis position in that half's key, so the deformation only fires
    on one side of the avatar. Useful for converting combined "Eye Blink"
    keys into the Left/Right pair Overte expects.
    """
    bl_idname = "object.overte_split_shape_key"
    bl_label = "Split Shape Key by Axis"
    bl_options = {"REGISTER","UNDO"}
    source_key: bpy.props.StringProperty(name="Source Shape Key", default="Eye Blink")
    left_name: bpy.props.StringProperty(name="Left Shape Key Name", default="")
    right_name: bpy.props.StringProperty(name="Right Shape Key Name", default="")
    center_epsilon: bpy.props.FloatProperty(
        name="Centerline Epsilon",
        description="Vertices within this distance of X=0 are kept in both halves",
        default=1e-5,
        min=0.0,
    )
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.data.shape_keys is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        shape_keys = obj.data.shape_keys.key_blocks
        source = shape_keys.get(self.source_key)
        if source is None:
            self.report({"ERROR"}, f"Shape key not found: {self.source_key}")
            return {"CANCELLED"}
        basis = shape_keys[0]
        left_name = self.left_name or f"{self.source_key}Left"
        right_name = self.right_name or f"{self.source_key}Right"
        if shape_keys.get(left_name) is not None or shape_keys.get(right_name) is not None:
            self.report({"ERROR"}, "Target shape key names already exist")
            return {"CANCELLED"}

        left_key = obj.shape_key_add(name=left_name, from_mix=False)
        right_key = obj.shape_key_add(name=right_name, from_mix=False)
        eps = self.center_epsilon
        for i in range(len(source.data)):
            basis_co = basis.data[i].co
            source_co = source.data[i].co
            side = axis_side(basis_co.x, eps)
            if side == "left":
                left_key.data[i].co = source_co
                right_key.data[i].co = basis_co
            elif side == "right":
                left_key.data[i].co = basis_co
                right_key.data[i].co = source_co
            else:
                left_key.data[i].co = source_co
                right_key.data[i].co = source_co
        self.report({"INFO"}, f"Created \"{left_name}\" and \"{right_name}\"")
        return {"FINISHED"}

def shape_key_menu_func(self, context):
    if self.layout is None:
        return
    self.layout.separator()
    self.layout.operator(SplitShapeKey.bl_idname, text="Split by Axis (Overte)")

class OverteAvatarPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__
    toes_required: bpy.props.BoolProperty(
        name="Treat toes as required",
        description="If enabled, ToeBase and Toe_End are surfaced as required bones in the TODO list",
        default=False,
    )
    def draw(self, context):
        self.layout.prop(self, "toes_required")

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
        try:
            toes_required = context.preferences.addons[__package__].preferences.toes_required
        except (KeyError, AttributeError):
            toes_required = False
        l.operator(RecalculateAllRolls.bl_idname, icon="FILE_REFRESH")
        l.separator()
        scene_armatures = [obj for obj in context.scene.objects if obj.type == "ARMATURE"]
        env_errors = []
        if len(scene_armatures) < 1:
            env_errors.append("Missing armature")
        elif len(scene_armatures) > 1:
            env_errors.append("Too many armatures")
        for mesh in context.active_object.children:
            for modifier in mesh.modifiers:
                if modifier.type != "ARMATURE":
                    env_errors.append(f"Mesh \"{mesh.name}\" has unsupported modifier named \"{modifier.name}\"")
        rule_errors, required_next, required_otherwise, optional_next, optional_otherwise = classify_bones(eb, toes_required)
        flow_errors = validate_flow_chains(eb)
        errors = env_errors + rule_errors + flow_errors

        needs_sep = False
        def layout_section(needs_sep,l,name,arr):
            if len(arr) == 0:
                return needs_sep
            if needs_sep:
                l.separator()
            l.label(text=f"{name}:")
            for item in arr:
                l.label(text=item)
            return True
        needs_sep = layout_section(needs_sep,l,"Errors",errors)
        needs_sep = layout_section(needs_sep,l,"Required Next",required_next)
        needs_sep = layout_section(needs_sep,l,"Required Otherwise",required_otherwise)
        needs_sep = layout_section(needs_sep,l,"Optional Next",optional_next)
        needs_sep = layout_section(needs_sep,l,"Optional Otherwise",optional_otherwise)

def menu_func(self,context):
    if self.layout is None:
        return
    l = self.layout
    l.separator()
    l.operator(AutoRename.bl_idname, text="Auto Rename")
    l.operator(AutoRename.bl_idname, text="Auto Rename and Reparent").do_reparent = True
    l.operator(AutoFlowBone.bl_idname, text="Auto Flow Bone")
    l.operator(RecalculateAllRolls.bl_idname, text="Recalculate All Rolls")

(c_register,c_unregister) = bpy.utils.register_classes_factory((
    OverteAvatarPrefs,
    AutoRename,
    AutoFlowBone,
    RecalculateAllRolls,
    SplitShapeKey,
    OverteAvatarTodoList,
))

_addon_keymaps = []

def _register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="Armature", space_type="EMPTY")
    a = km.keymap_items.new(AutoRename.bl_idname, type="FIVE", value="PRESS")
    b = km.keymap_items.new(AutoRename.bl_idname, type="SIX", value="PRESS")
    b.properties.do_reparent = True
    c = km.keymap_items.new(AutoFlowBone.bl_idname, type="SEVEN", value="PRESS")
    _addon_keymaps.extend([(km, a), (km, b), (km, c)])

def _unregister_keymaps():
    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()

def register():
    c_register()
    bpy.types.VIEW3D_MT_edit_armature.append(menu_func)
    shape_menu = getattr(bpy.types, "MESH_MT_shape_key_context_menu", None)
    if shape_menu is not None:
        shape_menu.append(shape_key_menu_func)
    _register_keymaps()

def unregister():
    _unregister_keymaps()
    shape_menu = getattr(bpy.types, "MESH_MT_shape_key_context_menu", None)
    if shape_menu is not None:
        shape_menu.remove(shape_key_menu_func)
    bpy.types.VIEW3D_MT_edit_armature.remove(menu_func)
    c_unregister()
