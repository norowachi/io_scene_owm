import bpy
from mathutils import Euler, Quaternion, Matrix, Vector
from .BLModel import GLOBAL_ROTATION
from ... import BoneUtil

def preprocessLoc(track, bone):
    for keyframe in track.keyframes:
        bone.matrix_basis.identity()
        if bone.parent:
            bone.matrix.translation = (bone.parent.matrix @ Vector(keyframe.data))
        else:
            bone.matrix_basis.translation = Vector(keyframe.data)
        keyframe.data = bone.location.copy()
        bone.matrix_basis.identity()

    return track

def preprocessRot(track, bone):
    for keyframe in track.keyframes:
        quat = Quaternion((keyframe.data[3], keyframe.data[0], keyframe.data[1], keyframe.data[2]))
        angle = quat.to_matrix().to_3x3()
        bone.matrix_basis.identity()
        if bone.parent is None:
            # I don't actually remember why this is here - probably
            # to set the root bone(s) to its rest pos / angle
            angle.rotate(GLOBAL_ROTATION)
            bone.matrix = angle.to_4x4()
            # print(bone.name)
        else:
            bone.matrix = (bone.parent.matrix.to_3x3() @ angle).to_4x4()
        keyframe.data = bone.rotation_quaternion.copy()
        bone.matrix_basis.identity()

    return track

def importTrack(track, bone, channel, action):
    path = bone.path_from_id(channel)

    for i, n in enumerate(track.keyframes[0].data):
        fcurve = action.fcurves.new(path, index=i)
        fcurve.keyframe_points.add(track.keyframeCount)
        
        
        for keyframeIndex, keyframe in enumerate(track.keyframes):
            fcurve.keyframe_points[keyframeIndex].co = keyframe.frame, keyframe.data[i]
            fcurve.keyframe_points[keyframeIndex].interpolation = 'LINEAR'


def importAction(animData, armature):
    #temp
    bpy.ops.object.mode_set(mode='POSE')

    action = bpy.data.actions.new(animData.GUID)
    
    armature.animation_data.action = action

    for animBone in animData.bones:
        remappedName = BoneUtil.getBoneName(animBone.name)
        if remappedName in armature.pose.bones:
            # was imported in version of addon with name remap
            animBone.name = remappedName

        if animBone.name not in armature.pose.bones:
            continue

        armatureBone = armature.pose.bones[animBone.name]
        armatureBone.matrix_basis.identity()
        if animBone.positions.keyframeCount:
            track = preprocessLoc(animBone.positions, armatureBone)
            importTrack(track, armatureBone, "location", action)

        if animBone.rotations.keyframeCount:
            track = preprocessRot(animBone.rotations, armatureBone)
            importTrack(track, armatureBone, "rotation_quaternion", action)

        if animBone.scale.keyframeCount:
            importTrack(animBone.scale, armatureBone, "scale", action)

    armature.animation_data.action = None
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return action