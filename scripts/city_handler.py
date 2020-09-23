import bpy
import os, pickle, time, logging
"""Script to create a random grid-city with corresponding blender-nodetree."""

# Road and building models to be implemented in City
road_bl_objects = [("SC road 1x1 1 straight instance", "STRAIGHT"),
                   ("SC road 1x1 1 intersect3 instance", "T_CROSSING"),
                   ("SC road 1x1 1 intersect4 instance", "X_CROSSING")]
buildings_bl_objects = [("SC building 4x4 5 instance", (4, 4)),
                        ("SC building 4x4 3 instance", (4, 4)),
                        ("SC building 4x4 2 instance", (4, 4)),
                        ("SC building 4x4 1 instance", (4, 4)),
                        ("SC building 4x4 5 instance", (4, 4)),
                        ("SC building 2x2 3 instance", (2, 2)),
                        ("SC building 2x2 2 instance", (2, 2)),
                        ("SC building 2x2 1 instance", (2, 2)),
                        ("SC building 1x1 1 instance", (1, 1)),
                        ("SC building 1x1 2 instance", (1, 1)),
                        ("SC building 1x1 3 instance", (1, 1)),
                        ("SC building 1x1 4 instance", (1, 1))]


# generalized blender-handler
def create_override(override):
    """Takes override arguments as dictionary and applies them to copy of current context"""
    override_context = bpy.context.copy()
    for key, value in override.items():
        override_context[key] = value
    return override_context


def toggle_expand(state):
    """state=1 expands all collections, state=2 collapses all collections"""
    area = next(a for a in bpy.context.screen.areas if a.type == 'OUTLINER')
    override_context = create_override({'area': area})
    bpy.ops.outliner.show_hierarchy(override_context, 'INVOKE_DEFAULT')
    for i in range(state):
        bpy.ops.outliner.expanded_toggle(override_context)
    area.tag_redraw()


def remove_collection(names):
    """Takes list of collection names and removes them."""
    for name in names:
        coll = bpy.data.collections.get(name)

        if coll:
            obs = [o for o in coll.objects if o.users == 1]
            while obs:
                bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)


def create_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)


# scenecity handler
def link_assets():
    """Load premade assets into blender. Then available via bpy.data."""
    # starting from empty scene
    # linking scenecity assets
    bpy.ops.scene.sc_op_link_assets()
    #bpy.ops.scene.sc_ot_append_template_cities()
    # hide and disable render for assets
    bpy.data.collections["Collection"].hide_viewport = True
    bpy.data.collections["Collection"].hide_render = True
    # toggling outliner
    toggle_expand(2)


def create_grid(nodetree, data_dir, grid_size=(10, 10), cell_size=10):  # ToDo-me: Seed parameter übergeben?
    """Create Grid and save its layout in data_dir"""
    # create and link nodes
    grid_node = nodetree.nodes.new("GridNode")
    grid_node.location = (-200, 0)
    grid_node.grid_size = grid_size
    grid_node.cell_size = cell_size
    map_creation_node = nodetree.nodes.new("NonOverlappingBoxesLayoutNode")
    map_creation_node.location = (200, 0)
    map_creation_node.boxes_values = "comm"
    nodetree.links.new(grid_node.outputs["Grid"], map_creation_node.inputs[0])

    # save grid for later access
    grid = map_creation_node.get_grid()  # type: Grid
    pickle.dump(grid.data, open(os.path.join(data_dir, 'grid.pkl'), 'wb'))
    logging.info(f'grid_size: {grid_size}, cell_size: {cell_size}')
    return map_creation_node


def add_roads(nodetree, grid_node, road_bl_objects):
    """Create roads to given grid using scencities nodes"""
    # take object names from SceneCity high-poly assets collection
    road_collector_node = nodetree.nodes.new("RoadPortionsCollectionNode")
    road_collector_node.location = (600, -500)

    for i, (name, kind) in enumerate(road_bl_objects):
        # ToDo-me: creating sockets manually instead of using defined blender/SC operator?
        new_socket = road_collector_node.inputs.new("WeightedRoadPortionSocket", "WeightedRoadPortion" + name)

        # add and link static road portions
        static_road_portion_node = nodetree.nodes.new("StaticRoadPortionNode")
        static_road_portion_node.location = (100, -i * 250 - 500)
        static_road_portion_node.type = kind

        nodetree.links.new(static_road_portion_node.outputs["Road portion"], new_socket)

        # add and link blender object getter nodes
        object_getter_node = nodetree.nodes.new("ObjectsGetterNode")
        object_getter_node.blender_object_name = name
        object_getter_node.location = (-200, -i * 250 - 500)
        nodetree.links.new(object_getter_node.outputs["Objects"], static_road_portion_node.inputs["Objects"])

    road_portions_instancer_node = nodetree.nodes.new("RoadPortionsInstancerNode")
    road_portions_instancer_node.location = (1000, -500)
    road_portions_instancer_node.grid_values_to_consider = 'road = all'
    nodetree.links.new(road_collector_node.outputs["Road portions"], road_portions_instancer_node.inputs["Road portions"])
    nodetree.links.new(grid_node.outputs["Grid"], road_portions_instancer_node.inputs["Grid"])

    object_instancer_node = nodetree.nodes.new("ObjectsInstancerNode")
    object_instancer_node.location = (1500, -500)
    object_instancer_node.blender_objects_name_prefix = "Roads"
    nodetree.links.new(road_portions_instancer_node.outputs["Objects"], object_instancer_node.inputs["Objects"])

    # use create operator
    source_node_path = 'bpy.data.node_groups["' + object_instancer_node.id_data.name + '"].' + object_instancer_node.path_from_id()
    bpy.ops.node.objects_instancer_node_create(source_node_path=source_node_path)


def add_buildings(nodetree, grid_node, buildings_bl_objects):
    buildings_collector_node = nodetree.nodes.new("BuildingsCollectionNode")
    buildings_collector_node.location = (600, -1500)

    for i, (name, size) in enumerate(buildings_bl_objects):
        new_socket = buildings_collector_node.inputs.new("WeightedBuildingSocket", "WeightedBuildingSocket" + name)

        # add and link static building portions
        static_building_node = nodetree.nodes.new("StaticBuildingNode")
        static_building_node.location = (100, -i*250-1500)
        static_building_node.size = size
        nodetree.links.new(static_building_node.outputs["Building"], new_socket)

        # add and link blender object getter nodes
        object_getter_node = nodetree.nodes.new("ObjectsGetterNode")
        object_getter_node.blender_object_name = name
        object_getter_node.location = (-200, -i * 250 - 1500)
        nodetree.links.new(object_getter_node.outputs["Objects"], static_building_node.inputs["Objects"])

    buildings_instancer_node = nodetree.nodes.new("BuildingsInstancerNode")
    buildings_instancer_node.location = (1000, -1500)
    buildings_instancer_node.grid_keys_values_restrict_any = "district = comm"
    nodetree.links.new(buildings_collector_node.outputs["Buildings"], buildings_instancer_node.inputs["Buildings"])
    nodetree.links.new(grid_node.outputs["Grid"], buildings_instancer_node.inputs["Grid"])

    object_instancer_node = nodetree.nodes.new("ObjectsInstancerNode")
    object_instancer_node.location = (1500, -1500)
    object_instancer_node.blender_objects_name_prefix = "Buildings"
    nodetree.links.new(buildings_instancer_node.outputs["Objects"], object_instancer_node.inputs["Objects"])

    # use create operator
    source_node_path = 'bpy.data.node_groups["' + object_instancer_node.id_data.name + '"].' + object_instancer_node.path_from_id()
    bpy.ops.node.objects_instancer_node_create(source_node_path=source_node_path)


def add_sky_texture(HDRI_base_dir, sky_HDRI):
    # bpy.context.area.ui_type = "ShaderNodeTree"
    # bpy.context.space_data.shader_type = "WORLD"
    node_tree = bpy.data.worlds["World"].node_tree
    tex_node = node_tree.nodes.new("ShaderNodeTexEnvironment")
    tex_node.location = (-300, 300)
    bpy.ops.image.open(filepath=os.path.join(HDRI_base_dir, sky_HDRI),
                       directory=HDRI_base_dir,
                       files=[{"name": sky_HDRI}], relative_path=True,
                       show_multiview=False)
    tex_node.image = bpy.data.images[sky_HDRI]
    background_node = node_tree.nodes["Background"]
    background_node.inputs[1].default_value = 2
    node_tree.links.new(tex_node.outputs["Color"], background_node.inputs["Color"])
    # bpy.context.area.ui_type = "NodeTree_SceneCity"


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def create_city(grid_size, road_bl_objects, buildings_bl_objects, data_dir, HDRI_base_dir, sky_HDRI) :
    """Follows steps on https://sites.google.com/view/scenecity16doc/grid-cities to create city."""
    logging.info('Start create_city')
    start_time = time.time()
    # deleting all objects
    clear_scene()
    link_assets()
    remove_collection(["SceneCity low-poly assets"])
    create_collection("City")
    # change context and create node tree
    # bpy.context.area.ui_type = "NodeTree_SceneCity"
    bpy.ops.node.new_node_tree(type="NodeTree_SceneCity")
    nodetree = bpy.data.node_groups["NodeTree"]
    final_grid_node = create_grid(nodetree, data_dir, grid_size=grid_size)
    # Define list of blender objects of roads tupled with their function (STRAIGHT, T_CROSSING, X_CROSSING)
    add_roads(nodetree, final_grid_node, road_bl_objects)
    add_buildings(nodetree, final_grid_node, buildings_bl_objects)
    add_sky_texture(HDRI_base_dir, sky_HDRI)
    # bpy.context.area.ui_type = "TEXT_EDITOR"
    logging.info(f'Created GridCity - execution Time: {time.time() - start_time} s')
    print(f'Created GridCity\nExecution Time: {time.time() - start_time} s')


if __name__ == "__main__":
    grid_size = (1, 1)
    HDRI_base_dir = r"/home/max/Documents/BA/HDRI"
    sky_HDRI = "CGSkies_0342_free.hdr"
    data_base_dir = r"/home/max/Documents/BA/program/scripts/data"
    create_city(grid_size, road_bl_objects, buildings_bl_objects, data_base_dir, HDRI_base_dir, sky_HDRI)
