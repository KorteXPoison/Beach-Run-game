from typing import List, Tuple

def my_obj_reader(filename: str) -> Tuple[List[List[float]], List[List[float]]]:
    """Get the vertices and UVs from the file"""
    position_list = []
    vertices = []

    list_uv = []
    uv = []

    with open(filename, 'r') as in_file:
        for line in in_file:
            if line.startswith('v '):
                point = [float(value) for value in line.strip().split()[1:]]
                vertices.append(point)
            elif line.startswith('vt'):
                p = [float(value) for value in line.strip().split()[1:]]
                uv.append(p)
            elif line.startswith('f'):
                face_description_position = [int(value.split('/')[0]) for value in line.strip().split()[1:]]
                face_description_UV = [int(value.split('/')[1]) if '/' in value and len(value.split('/')) > 1 and value.split('/')[1] else None for value in line.strip().split()[1:]]

                for i, elem in enumerate(face_description_position):
                    # Adjust for negative indices
                    if elem < 0:
                        elem += len(vertices)
                    else:
                        elem -= 1
                    
                    if 0 <= elem < len(vertices):
                        position_list.append(vertices[elem])
                    else:
                        print(f"Warning: position index {elem} out of range in line: {line.strip()}")

                for i, elem in enumerate(face_description_UV):
                    if elem is None:
                        continue  # Skip if there's no UV index
                    if elem < 0:
                        elem += len(uv)
                    else:
                        elem -= 1
                    
                    if 0 <= elem < len(uv):
                        list_uv.append(uv[elem])
                    else:
                        print(f"Warning: UV index {elem} out of range in line: {line.strip()}")

    return position_list, list_uv

if __name__ == '__main__':
    f_in = input("File? ")
    result = my_obj_reader(f_in)
    print(result)
