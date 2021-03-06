# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 13:48:41 2017

9/6/2017 Update

@author: Benjamin Pedigo
Computational Neuroanatomy Internship 
June - September, 2017
Allen Instititute for Brain Science

This module offers a variety of functions for interfacing blender with 3D 
meshes generated by the Princeton segmentation, as well as the synapse/graph 
data. 

"""

import numpy as np
import pandas as pd
import bpy

GRAPH_NAME = r'C:\Users\benjaminp\Desktop\NeuronReconstructions\graph\170605_nt_v11_mst_trimmed_sem_final_edges.csv'
CELL_NAME = r'C:\Users\benjaminp\Desktop\NeuronReconstructions\20170818_cell_list.csv'
STL_FOLDER = r'Z:\ben\20170818_ds10\\'

###############################################################################
def makeMaterial(name, diffuse, alpha):
    '''
    Creates a material in blender based on color and alpha intensity params
    
    https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Materials_and_textures
    
    name : str
    diffuse : RGB triplet, 0-1,  list like
    alpha : scalar 0 - 1
    
    '''
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT' 
    mat.diffuse_intensity = 1.0 
    mat.specular_color = diffuse
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.0
    mat.alpha = alpha
    mat.ambient = 1
    return mat

def create_materials():
    '''
    Initializes a set of materials in blender that will determine color of 
    neurons and synapse cubes
    '''
    
    spiny_neuron_mat = makeMaterial('spiny_neuron_mat', (1, 0, 0), 1)
    smooth_neuron_mat = makeMaterial('smooth_neuron_mat', (0, 0, 1), 1)
    #yellow
    all_box_mat = makeMaterial('all_box_mat', (0.8, 0.8, 0), 1)
    #pinkish
    spiny_box_mat = makeMaterial('spiny_box_mat', (0.8, 0.2, 0.45), 1)
    #pale blue
    smooth_box_mat = makeMaterial('smooth_box_mat', (0.35, 0.8, 0.8), 1)

def crappy_shifter(coord):
    '''
    Bad way of mapping graph coordinates to that used by the converted stl files
    Was mostly determined by looking at max/mins and trial and error, so likely 
    not quite exact. 
    
    Coord : 3 element iterable
    
    Returns: a list of x,y,z coordinates that should agree with stl coordinates
    
    '''
    
    shift = np.array([0.10245, 0.07687, 0])
    coord_shift = coord * 0.00001
    coord_shift = coord_shift - shift
    coord_shift[0] = coord_shift[0]*4
    coord_shift[1] = coord_shift[1]*4
    coord_shift[2] = coord_shift[2]*40
    return coord_shift

def process_df(graph_for_cell):
    '''
    input : dataframe
    
    output : list of xyz coordinates 
    '''
    
    coords=[]
    for i in range(graph_for_cell.shape[0]):
        coord = graph_for_cell.iloc[i,:]
        coord = coord.loc['locs_1':'locs_3'].as_matrix()
        coord_shift = crappy_shifter(coord)
        coords.append(coord_shift)
    return coords

def load_cell(cell_id, cell_type = '?'):
    '''
    Imports cell into blender
    
    Note: this function will likely have to be changed if the naming convention
    for .stls changes. Blender reads in something like '000000_ds10.stl' and 
    renames it internally to '000000 Ds10'.
    
    Note: added global variables fileconv and blendconv. These are the naming 
    conventions used by the two systems. Will always assume it starts with a 
    cell id, followed by whatever is specified in fileconv. blendconv must
    match how blender interprets the fileconv, see above note.
    
    cell_id : int,
        number of cell
    cell_type : str
        'E' or 'I'
    stl_folder : str
        path to where stls are stored 
    '''
    
    bpy.ops.import_mesh.stl(filepath = STL_FOLDER + str(cell_id) + fileconv)
    name = str(cell_id) + blendconv
    if cell_type == 'E':
        bpy.data.objects[name].data.materials.append(bpy.data.materials['spiny_neuron_mat'])
        bpy.data.objects[name].select = True 
    elif cell_type == 'I':
        bpy.data.objects[name].data.materials.append(bpy.data.materials['smooth_neuron_mat'])
        bpy.data.objects[name].select = True 
    print('Loaded .stl for cell %i' %(cell_id))

def create_vertices (name, verts):
    '''
    
    
    https://blender.stackexchange.com/questions/23086/add-a-simple-vertex-via-python 
    name : string
        new object name
    verts : array
        position coords - [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0),...]
    
    
    
    '''  
    # Create mesh and object
    me = bpy.data.meshes.new(name+'Mesh')
    ob = bpy.data.objects.new(name, me)
    ob.show_name = True
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    me.from_pydata(verts, [], [])
    # Update mesh with new data
    me.update() 
    return ob

def create_boxes(name, graph_for_cell):
    '''
    Creates a mesh containing all of the bounding boxes specified in the graph
    https://blender.stackexchange.com/questions/2407/how-to-create-a-mesh-programmatically-without-bmesh
    
    name : str
        title to give the boxes
    graph_for_cell : pandas dataframe
        currently works for format from '170605_nt_v11_mst_trimmed_sem_final_...
        edges.csv'
       
    '''
    
    all_verts = []
    all_faces = []
    for i in range(graph_for_cell.shape[0]):
        row = graph_for_cell.iloc[i,:]
        
        # lowest corner and highest corner of the synapse, respectively
        low_coord = row.loc['bboxes_1':'bboxes_3'].as_matrix()
        high_coord = row.loc['bboxes_4':'bboxes_6'].as_matrix()
        
        low_coord = crappy_shifter(low_coord)
        high_coord = crappy_shifter(high_coord)
        
        verts = [(low_coord[0], low_coord[1], low_coord[2]),
                 (low_coord[0], low_coord[1], high_coord[2]),
                 (low_coord[0], high_coord[1], high_coord[2]),
                 (low_coord[0], high_coord[1], low_coord[2]),
                 (high_coord[0], low_coord[1], low_coord[2]),
                 (high_coord[0], low_coord[1], high_coord[2]),
                 (high_coord[0], high_coord[1], high_coord[2]),
                 (high_coord[0], high_coord[1], low_coord[2])
                 ]
        
        # concatenate with other vertices 
        all_verts = all_verts + verts
        
        # used right hand rule to define direction just to be safe. 8*i is to 
        # account for the fact that indices referenced change as you concatenate
        faces = np.array([[0,1,2,3],[0,3,7,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[5,4,7,6]]) + 8*i
        faces = faces.tolist()
        all_faces = all_faces + faces
        
    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(all_verts, [], all_faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    scene.objects.link(obj)

def get_subgraphs(cell_id, inout):
    '''
    Returns 3 type of subgraphs for each cell
    
    cell_id : int
    inout : str
        'in' or 'out'
    
    Return : 3 pandas dataframes
        (all, smooth, spiny)
    '''
    if inout == 'in':
        all_graph = postsyn_cells_graph[postsyn_cells_graph.segs_2 == cell_id]
        smooth_graph = all_graph[all_graph['segs_1'].isin(smooth_cells)]
        spiny_graph = all_graph[all_graph['segs_1'].isin(spiny_cells)]
    elif inout == 'out':
        all_graph = presyn_cells_graph[presyn_cells_graph.segs_1 == cell_id]
        smooth_graph = all_graph[all_graph['segs_2'].isin(smooth_cells)]
        spiny_graph = all_graph[all_graph['segs_2'].isin(spiny_cells)]
    
    return all_graph, smooth_graph, spiny_graph

def load_syns(cell_id, inout, output_vertices = False, output_boxes = True):
    '''
    For a given cell and in/out behavior, can load synapse vertices or bounding
    boxes into blender. 
    
    Parameters
    ----------
    cell_id : int
    inout : str
        'in' or 'out'
    output_vertices : bool 
    output_boxes : bool     
    '''
    
    
    all_graph, smooth_graph, spiny_graph = get_subgraphs(cell_id, inout)
    
    smooth_coords = process_df(smooth_graph)
    spiny_coords = process_df(spiny_graph)
    all_coords = process_df(all_graph)
    
    if output_vertices:
        if len(all_coords) > 0:
            name = str(cell_id) + '_' + inout + '_all'
            create_vertices(name, tuple(all_coords))
            bpy.data.objects[name].select = True 
            if len(smooth_coords) > 0:
                name = str(cell_id) + '_' + inout + '_smooth' 
                create_vertices(name ,tuple(smooth_coords))
                bpy.data.objects[name].select = True 
            if len(spiny_coords) > 0:
                name = str(cell_id) + '_' + inout + '_spiny'
                create_vertices(name, tuple(spiny_coords))
                bpy.data.objects[name].select = True 
    
    if output_boxes:
        if all_graph.shape[0] > 0:
            name = str(cell_id) + '_' + inout + '_all_boxes'
            create_boxes(name, all_graph)
            bpy.data.objects[name].data.materials.append(bpy.data.materials['all_box_mat'])
            bpy.data.objects[name].select = True 
            if smooth_graph.shape[0] > 0:    
                name = str(cell_id) + '_' + inout + '_smooth_boxes'
                create_boxes(name, smooth_graph)
                bpy.data.objects[name].data.materials.append(bpy.data.materials['smooth_box_mat'])
                bpy.data.objects[name].select = True 
            if spiny_graph.shape[0] > 0:
                name = str(cell_id) + '_' + inout + '_spiny_boxes'
                create_boxes(name, spiny_graph)
                bpy.data.objects[name].data.materials.append(bpy.data.materials['spiny_box_mat'])
                bpy.data.objects[name].select = True 
    
    if inout == 'in':
        print('Loaded %i input synapses. %i from smooth, %i from spiny.' %(len(all_coords), len(smooth_coords), len(spiny_coords)))
    if inout == 'out':
        print('Loaded %i output synapses. %i to smooth, %i to spiny.' %(len(all_coords), len(smooth_coords), len(spiny_coords)))
    
def get_cell_type(cell_id):
    indx = np.where(cell_id_array == cell_id)[0][0]
    return cell_type_array[indx]

def load_neighbors(cell_id, adj='all',):
    '''
    Loads the cells that connect to a given cell. Type of connection can be 
    specified using 'adj'
    
    cell_id : int
    adj : str
        In the following options, _(spiny/smooth) refers to connections from or 
        onto a smooth or spiny cell
        'all'
        'in'
        'in_spiny'
        'in_smooth'
        'out'
        'out_spiny'
        'out_smooth'
    '''
    
    if adj == 'all':
        in_all_graph, in_smooth_graph, in_spiny_graph = get_subgraphs(cell_id, 'in')
        in_specific = pd.concat([in_smooth_graph, in_spiny_graph])
        in_neighbors = in_specific.loc[:, 'segs_1'].as_matrix()
        
        out_all_graph, out_smooth_graph, out_spiny_graph = get_subgraphs(cell_id, 'out')
        out_specific = pd.concat([out_smooth_graph, out_spiny_graph])
        out_neighbors = out_specific.loc[:, 'segs_2'].as_matrix()
        neighbors = np.concatenate((in_neighbors, out_neighbors))
        neighbors = np.unique(neighbors)
        for neighbor in neighbors:
            load_cell(neighbor, get_cell_type(neighbor))
    elif adj == 'in':
        in_all_graph, in_smooth_graph, in_spiny_graph = get_subgraphs(cell_id, 'in')
        in_specific = pd.concat([in_smooth_graph, in_spiny_graph])
        in_neighbors = in_specific.loc[:, 'segs_1'].as_matrix()
        
        neighbors = np.unique(in_neighbors)
        for neighbor in neighbors:
            load_cell(neighbor, get_cell_type(neighbor))
    elif adj == 'out':
        out_all_graph, out_smooth_graph, out_spiny_graph = get_subgraphs(cell_id, 'out')
        out_specific = pd.concat([out_smooth_graph, out_spiny_graph])
        out_neighbors = out_specific.loc[:, 'segs_2'].as_matrix()
        
        neighbors = np.unique(out_neighbors)
        for neighbor in neighbors:
            load_cell(neighbor, get_cell_type(neighbor))
            
def load_cell_and_syns(cell_id,):
    '''
    Function that combines 'load_cell()' and 'load_syns()', loading a given 
    and its bounding box mesh all at once. 
    
    cell_id : str   
    
    '''
    
    load_cell(cell_id, get_cell_type(cell_id))
    load_syns(cell_id, 'in')
    load_syns(cell_id, 'out')
    bpy.ops.group.create(name = str(cell_id) + '_with_syns')

def clear_all():
    '''
    Deletes all objects in blender
    '''
    for obj in bpy.data.objects:
        obj.select = True
    bpy.ops.object.delete()


'''
The following 3 functions were a small utility I made to estimate the centers 
of cells without having to write coordinates down manually. It estimates the 
center of the soma by having the user place the cursor at the 'center' based on 
3 different viewpoints, and then averages the position from those 3. 

Not very user friendly, but happy to answer questions if anyone has them. Seems
difficult to take in user input on the console in blender, so I resorted to
repeating the same console commands over and over. 
'''
def next_cell(i, soma_coords, cell_coords):
    loc = r'C:\Users\benjaminp\Desktop\NeuronReconstructions\20170818_cells_soma_loc.csv'
    if i > -1:
        soma_x = (soma_coords[0,0] + soma_coords[2,0]) / 2.0
        soma_y = (soma_coords[1,1] + soma_coords[2,1]) / 2.0
        soma_z = (soma_coords[0,2] + soma_coords[1,2]) / 2.0
        cell_coords[i, :] = [soma_x, soma_y, soma_z] 
        np.savetxt(loc, cell_coords, delimiter= ",")
    i = i + 1
    clear_all()
    load_cell(cell_id_array[i])
    soma_coords = np.zeros((3,3))
    return i, soma_coords, cell_coords

def xz(soma_coords):
    coords = bpy.context.scene.cursor_location
    soma_coords[0, :] = coords
    print(soma_coords)
    return soma_coords

def yz(soma_coords):
    coords = bpy.context.scene.cursor_location
    soma_coords[1, :] = coords
    print(soma_coords)
    return soma_coords    

def xy(soma_coords):
    coords = bpy.context.scene.cursor_location
    soma_coords[2, :] = coords
    print(soma_coords)
    return soma_coords

###############################################################################
# lists of cells that can also be called from the blender console
# also used by some functions 
full_graph = pd.read_csv(GRAPH_NAME)

cell_list = pd.read_csv(CELL_NAME)
cell_id_array = cell_list.as_matrix(columns = ['cell_id'])
cell_id_array = cell_id_array.flatten()
all_cells = cell_id_array

cell_type_array = cell_list.as_matrix(columns = ['cell_type'])
cell_type_array = cell_type_array.flatten()

presyn_cells_graph = full_graph[full_graph['segs_1'].isin(cell_id_array)]
postsyn_cells_graph = full_graph[full_graph['segs_2'].isin(cell_id_array)]

smooth_cells = cell_id_array[cell_type_array == 'I']
smooth_cells = smooth_cells.flatten()

spiny_cells = cell_id_array[cell_type_array == 'E']
spiny_cells = spiny_cells.flatten()

fileconv = '_ds10.stl'
blendconv = ' Ds10'