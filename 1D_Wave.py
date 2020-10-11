# https://blender.stackexchange.com/questions/36902/how-to-keyframe-mesh-vertices-in-python
# https://gist.github.com/zeffii/5593f5aab165de8d2043
# https://blender.stackexchange.com/questions/61879/create-mesh-then-add-vertices-to-it-in-python/159185
# https://blender.stackexchange.com/questions/36933/efficient-way-to-delete-all-points-below-z-0-on-grid-via-python-script?rq=1

import bpy
from mathutils import Vector
import bmesh
import numpy as np

# parameters

n_frames = 100

resolution = 10
k_x = 4
omega = 2  
vpack = 1 # packet velocity
sigma = 0.25 # broadening
bpy.context.scene.frame_end = n_frames
x0 = 2 # starting coord for wave packet
FPS = 24
x_size = 2

# add plane

print("add plane")
"""
bpy.ops.mesh.primitive_plane_add(size=4.0, calc_uvs=True, enter_editmode=True,align='WORLD')
"""

bpy.ops.curve.primitive_nurbs_path_add(radius=1.0, enter_editmode=True, align='WORLD')
bpy.ops.curve.subdivide(number_cuts=resolution)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.convert(target='MESH')

bpy.ops.object.mode_set(mode='EDIT')

bpy.ops.mesh.select_mode( type  = 'EDGE'   )
bpy.ops.mesh.select_all( action = 'SELECT' )

bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value":(0, 1, 0)}
)

plane = bpy.context.active_object

plane.name = "WavePlane"
me = plane.data


bpy.ops.object.mode_set(mode='OBJECT')




plane_vertices = np.array([v.co for v in me.vertices]) # get plane vertices

print(plane_vertices.shape)

xmin, xmax = plane_vertices[:,0].min(), plane_vertices[:,0].max()
ymin, ymax = plane_vertices[:,1].min(), plane_vertices[:,1].max()
zmin, zmax = plane_vertices[:,2].min(), plane_vertices[:,2].max()

print("xmin, xmax: ",xmin,xmax)
print("ymin, ymax: ",ymin,ymax)
print("zmin, zmax: ",zmin,zmax)

zc = np.linspace(zmin, zmax, n_frames)
new_plane_vertices = np.zeros_like(plane_vertices)

# pad pristine copy of the plane as first element and last element of data.
data = [plane_vertices.copy()]


for f in range(n_frames):
    t = f/FPS;
#    new_plane_vertices[:,:2] = (1.0 + np.exp(-(plane_vertices[:,2] - zc[i])**2/(2.*sig**2)))[:,None] * plane_vertices[:,:2]
#    new_plane_vertices[:,2] = plane_vertices[:,2]
    new_plane_vertices[:,2] = np.sin(2*np.pi*(k_x*plane_vertices[:,0]-omega*t)) * \
        1/(2*np.sqrt(2*np.pi)*sigma) * np.exp( -(x0+plane_vertices[:,0]  - vpack * t)**2/(2*sigma**2))
    new_plane_vertices[:,0] = plane_vertices[:,0]
    new_plane_vertices[:,1] = plane_vertices[:,1]
    data.append(new_plane_vertices.copy())
data.append(plane_vertices.copy())



def insert_keyframe(fcurves, frame, values):
    for fcu, val in zip(fcurves, values):
        fcu.keyframe_points.insert(frame, val, options = {'FAST'})

action = bpy.data.actions.new("MeshAnimation")
me.animation_data_create()
me.animation_data.action = action

data_path = "vertices[%d].co"
vec_z = Vector((0.0, 0.0, 1.0))

frames = list(range(n_frames+2))

for index, v in enumerate(me.vertices):
    fcurves = [action.fcurves.new(data_path % v.index, index = i) for i in range(3)]
    co_rest = v.co

    for t in frames:
        co_kf = data[t][index]
        insert_keyframe(fcurves, t, co_kf)
