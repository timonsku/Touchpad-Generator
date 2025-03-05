import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from itertools import tee, islice, chain
import ezdxf

# all units in mm
# total width of via with annular ring
viaSize = 0.4
viaDrill = 0.3
# how far away from a diamond corner the via should be placed, this takes viaSize into account
viaOffset = 0.1
# width of the connecting traces
traceWidth = 0.1
# the outer line width of the polygon fills
# also affects minimum feature size for flood fill (in Eagle itself, other EDA likely ignores it)
polygonLineWidth = 0.005
dxf_path = 'touchpad.dxf'
# we use this file as our basis and add the routed Touchpad to it
boardFile = 'empty.brd'
schematicFile = 'empty.sch'

def parse_dxf_polygons(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    lines = []
    for entity in msp.query('LINE'):
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        lines.append((start, end))

    # Group lines into polygons
    polygons = []
    while lines:
        polygon = []
        current_line = lines.pop(0)
        polygon.append(current_line[0])
        polygon.append(current_line[1])

        while True:
            for i, line in enumerate(lines):
                if line[0] == polygon[-1]:
                    polygon.append(line[1])
                    lines.pop(i)
                    break
                elif line[1] == polygon[-1]:
                    polygon.append(line[0])
                    lines.pop(i)
                    break
            else:
                break
        # Remove duplicate vertices
        polygon = list(dict.fromkeys(polygon))
        polygons.append(polygon)

    return polygons

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

# for extracting polygons from an existing board file
# def parse_vertex(vertex):
#     return float(vertex.attrib['x']), float(vertex.attrib['y'])

def col_poly_is_up(polygon):
    if len(polygon) != 3:
        return False
    y_coords = [vertex[1] for vertex in polygon]
    y_coords.sort()
    return y_coords[1] < y_coords[2]

def col_poly_is_down(polygon):
    if len(polygon) != 3:
        return False
    y_coords = [vertex[1] for vertex in polygon]
    return y_coords[0] < y_coords[1]

def row_poly_is_left(polygon):
    if len(polygon) != 3:
        return False
    x_coords = [vertex[0] for vertex in polygon]
    return x_coords[0] < x_coords[1]

def row_poly_is_right(polygon):
    if len(polygon) != 3:
        return False
    x_coords = [vertex[0] for vertex in polygon]
    return x_coords[1] < x_coords[2]


def calculate_center(polygon):
    x_coords = [vertex[0] for vertex in polygon]
    y_coords = [vertex[1] for vertex in polygon]
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    return center_x, center_y

def group_polygons_by_center(polygons, axis='x'):
    groups = defaultdict(list)
    for polygon in polygons:
        center_x, center_y = calculate_center(polygon)
        key = round(center_x, 2) if axis == 'x' else round(center_y, 2)
        groups[key].append(polygon)
    return groups

def create_column(index, polygons):
    signal = ET.Element('signal', name=f'COL{index}')
    center_x_first, center_y_first = calculate_center(polygons[0])
    pad_element = ET.Element('element', name=f'COL{index}', library="touchpad", package="PAD_0_5MM", value="", x='{:.10f}'.format(center_x_first), y='{:.10f}'.format(center_y_first), smashed="yes")
    contactref_element = ET.Element('contactref', element=f'COL{index}', pad="P1")
    signal.append(contactref_element)
    for polygon_prev, polygon, polygon_next in previous_and_next(polygons):
        polygon_element = ET.Element('polygon', width='{:.10f}'.format(polygonLineWidth), layer="1", pour="solid", thermals="no")
        
        for vertex in polygon:
            vertex_element = ET.Element('vertex', x='{:.10f}'.format(vertex[0],8), y='{:.10f}'.format(vertex[1],8))
            polygon_element.append(vertex_element)
        signal.append(polygon_element)
        center_x, center_y = calculate_center(polygon)
        
        y_coords = [vertex[1] for vertex in polygon]
        y_coords.sort()
        if polygon_next is not None:
            y_coords_next = [vertex[1] for vertex in polygon_next]
            y_coords_next.sort()
        # print(f"  Center: ({center_x}, {center_y}), Y-coords: {y_coords}")
        if len(polygon) == 3:
            if col_poly_is_up(polygon):
                via_element = ET.Element('via', x='{:.10f}'.format(center_x), y='{:.10f}'.format(y_coords[2]-(viaSize+viaOffset)), extent="1-16", drill='{:.10f}'.format(viaDrill), diameter='{:.10f}'.format(viaSize))
                signal.append(via_element)
                wire_element = ET.Element('wire', x1='{:.10f}'.format(center_x), y1='{:.10f}'.format(y_coords[2]-(viaSize+viaOffset)), x2='{:.10f}'.format(center_x), y2='{:.10f}'.format(y_coords_next[0]+(viaSize+viaOffset)), width='{:.10f}'.format(traceWidth), layer="16")
                signal.append(wire_element)
            else:
                via_element = ET.Element('via', x='{:.10f}'.format(center_x), y='{:.10f}'.format(y_coords[0]+(viaSize+viaOffset)), extent="1-16", drill='{:.10f}'.format(viaDrill), diameter='{:.10f}'.format(viaSize))
                signal.append(via_element)
        elif len(polygon) == 4:
            # bottom via
            via_element = ET.Element('via', x='{:.10f}'.format(center_x), y='{:.10f}'.format(y_coords[0]+(viaSize+viaOffset)), extent="1-16", drill='{:.10f}'.format(viaDrill), diameter='{:.10f}'.format(viaSize))
            signal.append(via_element)
            # top via
            via_element = ET.Element('via', x='{:.10f}'.format(center_x), y='{:.10f}'.format(y_coords[3]-(viaSize+viaOffset)), extent="1-16", drill='{:.10f}'.format(viaDrill), diameter='{:.10f}'.format(viaSize))
            signal.append(via_element)
            # connect top via to the next polygons bottom via
            wire_element = ET.Element('wire', x1='{:.10f}'.format(center_x), y1='{:.10f}'.format(y_coords[3]-(viaSize+viaOffset)), x2='{:.10f}'.format(center_x), y2='{:.10f}'.format(y_coords_next[0]+(viaSize+viaOffset)), width='{:.10f}'.format(traceWidth), layer="16")
            signal.append(wire_element)
    return signal, pad_element

def create_row(index, polygons):
    signal = ET.Element('signal', name=f'ROW{index}')
    center_x_first, center_y_first = calculate_center(polygons[0])
    pad_element = ET.Element('element', name=f'ROW{index}', library="touchpad", package="PAD_0_5MM", value="", x='{:.10f}'.format(center_x_first), y='{:.10f}'.format(center_y_first), smashed="yes")
    contactref_element = ET.Element('contactref', element=f'ROW{index}', pad="P1")
    signal.append(contactref_element)
    for polygon_prev, polygon, polygon_next in previous_and_next(polygons):
        polygon_element = ET.Element('polygon', width='{:.10f}'.format(polygonLineWidth), layer="1", pour="solid", thermals="no")
        
        for vertex in polygon:
            vertex_element = ET.Element('vertex', x='{:.10f}'.format(vertex[0],8), y='{:.10f}'.format(vertex[1],8))
            polygon_element.append(vertex_element)
        signal.append(polygon_element)
        center_x, center_y = calculate_center(polygon)
        if polygon_next is not None:
            center_x_next, center_y_next = calculate_center(polygon_next)
            if not row_poly_is_left(polygon):
                # connect polygons on same layer, no vias for rows
                wire_element = ET.Element('wire', x1='{:.10f}'.format(center_x), y1='{:.10f}'.format(center_y), x2='{:.10f}'.format(center_x_next), y2='{:.10f}'.format(center_y_next), width='{:.10f}'.format(traceWidth), layer="1")
                signal.append(wire_element)

    return signal, pad_element

def generate_schematic(rows, columns):
    tree = ET.parse(schematicFile)
    root = tree.getroot()
    parts_element = root.find('.//parts')
    instances_element = root.find('.//instances')
    nets_element = root.find('.//nets')
    for row in range(1, rows):
        # <part name="TP1" library="touchpad" deviceset="TESTPOINT" device="PAD_0_5MM"/>
        part_element = ET.Element('part', name=f'ROW{row}', library="touchpad", deviceset="TESTPOINT", device="PAD_0_5MM")
        parts_element.append(part_element)
        instance_element = ET.Element('instance', part=f'ROW{row}', gate="G1", x=f"{45.72+row*2.54}", y="0.00", smashed="yes")
        attribute_element = ET.Element('attribute', name="NAME", x=f"{45.72+row*2.54}", y="6.0", size="1.27", layer="95", rot="R90", align="center-left")
        instance_element.append(attribute_element)
        instances_element.append(instance_element)
        net_element = ET.Element('net', {'name':f'ROW{row}','class':'0'})
        segment_element = ET.Element('segment')
        pinref_element = ET.Element('pinref', part=f'ROW{row}', gate="G1", pin="P1")
        segment_element.append(pinref_element)
        net_element.append(segment_element)
        nets_element.append(net_element)
    for column in range(1, columns):
        part_element = ET.Element('part', name=f'COL{column}', library="touchpad", deviceset="TESTPOINT", device="PAD_0_5MM")
        parts_element.append(part_element)
        instance_element = ET.Element('instance', part=f'COL{column}', gate="G1", x=f"{45.72+column*2.54}", y="20.32", smashed="yes")
        attribute_element = ET.Element('attribute', name="NAME", x=f"{45.72+column*2.54}", y="26.32", size="1.27", layer="95", rot="R90", align="center-left")
        instance_element.append(attribute_element)
        instances_element.append(instance_element)
        net_element = ET.Element('net', {'name':f'COL{column}','class':'0'})
        segment_element = ET.Element('segment')
        pinref_element = ET.Element('pinref', part=f'COL{column}', gate="G1", pin="P1")
        segment_element.append(pinref_element)
        net_element.append(segment_element)
        nets_element.append(net_element)
    tree.write('Touchpad.sch')
        
        
    
    

def main():
    tree = ET.parse(boardFile)
    root = tree.getroot()
    polygons = []
    
    # if you got a board file from a vendor with polygons you can use that instead of the dxf file
    # uncomment the parse_vertex function and the for loop below
    # for polygon in root.findall('.//board/plain/polygon'):
    #     vertices = [parse_vertex(vertex) for vertex in polygon.findall('vertex')]
    #     polygons.append(vertices)

    
    polygons = parse_dxf_polygons(dxf_path)
    print(f"Found {len(polygons)} polygons in the DXF file")

    columns = group_polygons_by_center(polygons, axis='x')
    rows = group_polygons_by_center(polygons, axis='y')

    sorted_columns = sorted(columns.items())
    print(f"Columns : {math.ceil(len(sorted_columns)/2)-1}")

    sorted_rows = sorted(rows.items())
    print(f"Rows : {math.ceil(len(sorted_rows)/2)-1}")

    generate_schematic(math.ceil(len(sorted_rows)/2), math.ceil(len(sorted_columns)/2))

    signals_element = root.find('.//signals')
    components_element = root.find('.//elements')
    if signals_element is None:
        signals_element = ET.SubElement(root.find('.//board'), 'signals')

    # we only want the odd columns and rows, the even ones are "fake" rows/columns e.g. part of the other row/column
    for column_index, (column, polygons) in enumerate(sorted_columns):
        polygons.sort(key=lambda p: calculate_center(p)[1])
        if column_index % 2 == 1:
            # print(f"Column {math.ceil(column_index/2)} is pointing upwards")
            signal_element, pad_element = create_column(math.ceil(column_index/2), polygons)
            signals_element.append(signal_element)
            components_element.append(pad_element)

    for row_index, (row, polygons) in enumerate(sorted_rows):
        polygons.sort(key=lambda p: calculate_center(p)[0])
        if row_index % 2 == 1:
            # print(f"Row {math.ceil(row_index/2)} is pointing sideways")
            signal_element, pad_element = create_row(math.ceil(row_index/2), polygons)
            signals_element.append(signal_element)
            components_element.append(pad_element)

    # delete all non signal polygons from the board file if you used a pre-populated board file
    # plain_polygons = root.find('.//plain')
    # for child in list(plain_polygons):
    #     if child.tag == 'polygon':
    #         plain_polygons.remove(child)

    tree.write('Touchpad.brd')

if __name__ == "__main__":
    main()


