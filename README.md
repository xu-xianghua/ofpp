# Openfoamparser
This is a simple Python library for parsing result or mesh files in OpenFOAM output files to Numpy arrays. Both ascii and binary format are supported.

## Installation

Install with pip:

```shell
pip install openfoamparser
```

or install with setup.py by:

```shell
python setup.py install
```

This package requires numpy.

## APIs

### parse field data

- parse_internal_field(fn):  parse internal field data from file **fn**, and return field data as numpy.array
- parse_boundary_field(fn): parse boundary field data from file **fn**, return boundary dictionary with boundary name as keys and Numpy.array as values.
- parse_field_all(fn): parse internal field data and boundary field data from file **fn**.

### parse mesh

Class FoamMesh can parse mesh data (in ascii or binary format) and provide inquiry.

#### instantiation 

- FoamMesh(path): initialization of class, read and parse mesh data (points, boundary, owner, neighbour, faces)  from path/constant/polyMesh

#### instance variables

- points:  Numpy.array, coordinates of points, in order of point id, read from mesh file **points**
- owner:  a list, the owner cell id of each face, in order of face id, read from mesh file **owner**
- neighbour:  a list, the neighbour cell id of each face, read from mesh file **neighbour**. For faces on boudary, their neighbours are boundary's id.
- faces: list of list, the ids of points composed the face, in order of face id, read from mesh file **faces**
- boundary: dictionary, with key of boundary name, value of a namedtuple, `namedtuple('Boundary', 'type, num, start, id')`, in which num is face numer, start is the id of start face, id is the boundary id, equals to `-10 - index`.
- num_point: points number
- num_face: face number
- num_inner_face:  inner face number
- num_cell: cell number
- cell_centres: Numpy.array, cell centre coordinates, read from field file, default is None
- cell_volumes: Numpy.array, cell volumes, read from field file, None for default
- face_areas: Numpy.array, face areas, read from field file, None for default
- cell_neighours: list of list, cell neibour cells' id, in order of cell id
- cell_faces: list of list, cell's face id, in order of cell id

#### class methods

- parse_points_content(content): parse points data from mesh file's content, in binary mode
- parse_owner_neighbour_content(content): parse owner or neighbour data from mesh file's content, in binary mode
- parse_faces_content(content): parse faces data from mesh file's content, in binary mode
- parse_boundary_content(content): parse boundary data from mesh file's content, in binary mode

#### mesh inquiry interface

- cell_neighbour_cells(i): return cell neighbours' id of cell i, in list
- boundary_cells(bd): return a generator of cell's id adjacent to boundary **bd**
- is_cell_on_boundary(i, bd): check if cell i is on boundary **bd**. if **bd** is None, check all boundaries.
- is_face_on_boundary(i, bd): check if face i is on boundary **bd**. if **bd** is None, check all boundaries.

## Usage

```python
import Ofpp
V = Ofpp.parse_internal_field('0/V')
wb01 = Ofpp.parse_boundary_field('0.1/alpha.water')
U02,Ub02 = Ofpp.parse_field_all('0.2/U')
mesh = Ofpp.FoamMesh('.')
wall_cells = list(mesh.boundary_cells(b'fixedWall'))
cell_neighbour_5 = mesh.cell_neighbour_cells(5)
```



## Tutorial

### prepare data of OpenFOAM

We use $FOAM_TUTORIALS/multiphase/interFoam/laminar/damBreak/damBreak for the demo.

```shell
➜ cp $FOAM_TUTORIALS/multiphase/interFoam/laminar/damBreak/damBreak .
➜ cd damBreak
➜ ./Allrun
➜ ls
0     0.1   0.2   0.3   0.4   0.5   0.6   0.7   0.8   0.9   1         Allrun    log
0.05  0.15  0.25  0.35  0.45  0.55  0.65  0.75  0.85  0.95  Allclean  constant  system
➜ ls 0.6
 alphaPhi0.water  alpha.water  p  phi  p_rgh  U  uniform
```

We use postProcess to generate cell volume data, which is written to file '0/V'

```shell
➜ postProcess -func 'writeCellVolumes' -time 0
➜ ls 0
alpha.water  alpha.water.orig  p_rgh  U  V
```

### Use Ofpp to process data

Firstly, use function `parse_internal_field` to parse '0/V' and get cell volume data,

```python
>>> import Ofpp
>>> V=Ofpp.parse_internal_field('0/V')
>>> V.shape
(2268,)
>>> sum(V)
0.0049626061800001099
>>> max(V)
2.6281599999999998e-06
>>> min(V)
1.11212e-06
>>>
```

Parse alpha.water to get water's volume fraction,

```python
>>> W0=Ofpp.parse_internal_field('0/alpha.water')
>>> W0.shape
(2268,)
>>> sum(W0*V)
0.00064609979999999856
>>> W01=Ofpp.parse_internal_field('0.1/alpha.water')
>>> sum(W01*V)
0.00064609986628872621
>>> max(W0)
1.0
>>>
```

Parse alpha.water of all time steps, and calculate water volume of each time to check mass ballance: 

```python
>>> import numpy as np
>>> Wa=[]
>>> for t in np.arange(0, 1.01, 0.05):
...     Wa.append(Ofpp.parse_internal_field('%.4g/alpha.water'%t))
>>> ["{:.5g}".format(sum(x*V)) for x in Wa]
['0.0006461', '0.0006461', '0.0006461', '0.0006461', '0.0006461', '0.0006461', '0.0006461', '0.00064307', '0.00064047', '0.00063953', '0.00063297', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171', '0.00063171']
>>> import matplotlib.pyplot as pl
>>> pl.plot(np.arange(0, 1.01, 0.05), [sum(x*V) for x in Wa], 's-')
```

Parse velocity field, which is a vector field. And calculate the velocity magnitude,

```python
>>> U01=Ofpp.parse_internal_field('0.1/U')
>>> U01.shape
(2268, 3)
>>> U01[50]
array([ 0.280417 , -0.0783402,  0.       ])
>>> v01=(U01[:,0]**2+U01[:,1]**2+U01[:,2]**2)**0.5
>>> v01[50]
0.29115439344966104
```

Noticing that some fields are uniform, eg. initial velocity, whose data is a vector,

```python
>>> U0=Ofpp.parse_internal_field('0/U')
>>> U0
array([ 0.,  0.,  0.])
>>>
```



### boundary data

Boundary data parsed by Ofpp is a dictionary because there are usually more than one boundary entities.  Its keys are boundary names and values are also dictionaries.

```python
>>> b01=Ofpp.parse_boundary_field('0.1/alpha.water')
>>> b01.keys()
dict_keys([b'rightWall', b'atmosphere', b'leftWall', b'lowerWall', b'defaultFaces'])
>>> b01[b'atmosphere'].keys()
dict_keys([b'inletValue', b'value'])
>>> b01[b'atmosphere'][b'inletValue']
0.0
>>> b01[b'atmosphere'][b'value'].shape
(46,)
>>> b01[b'atmosphere'][b'value']
array([  0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
         0.00000000e+00,   0.00000000e+00,   6.48450000e-54,
         1.03531000e-52,   3.02802000e-53,   1.67528000e-53,
         9.36177000e-54,   4.89156000e-54,   2.18620000e-54,
         5.33282000e-55,   8.91129000e-56,   1.13156000e-56,
         1.13522000e-57,   9.31454000e-59,   6.39173000e-60,
         3.72975000e-61,   1.85390000e-62,   8.04808000e-64,
         3.10349000e-65,   1.01620000e-66,   2.83696000e-68,
         6.78134000e-70,   1.35776000e-71,   2.23345000e-73,
         2.92040000e-75,   2.88435000e-77,   1.93630000e-79,
         5.49169000e-82])
>>>
```

### mesh

Create a FoamMesh object and read mesh file.

```python
>>> mesh = Ofpp.FoamMesh('.')
>>> mesh.num_face
9176
>>> mesh.num_inner_face
4432
>>> mesh.num_cell
2267
>>> mesh.num_point
4746
>>> mesh.boundary
{b'lowerWall': Boundary(type=b'wall', num=62, start=4532, id=-12), 
 b'rightWall': Boundary(type=b'wall', num=50, start=4482, id=-11), 
 b'atmosphere': Boundary(type=b'patch', num=46, start=4594, id=-13), 
 b'defaultFaces': Boundary(type=b'empty', num=4536, start=4640, id=-14), 
 b'leftWall': Boundary(type=b'wall', num=50, start=4432, id=-10)}
>>>

```

Read outside data for cell volumes, cell centers

```python
>>> mesh.read_cell_volumes('0/V')
>>> mesh.read_cell_centres('0/C')
                           
```

Mesh inquiry:

```python
>>> mesh.cell_neighbour_cells(300)
[281, 299, 301, 319, -14, -14]
>>> mesh.cell_faces[134]
[263, 264, 4797, 4981, 219, 261]
>>> cell_to_wall=list(mesh.boundary_cells(b'leftWall'))
>>> len(cell_to_wall)
50
>>> mesh.is_cell_on_boundary(545)
True
>>> mesh.is_cell_on_boundary(545, b'atmosphere')
False
>>> mesh.is_face_on_boundary(334, b'leftWall')
False
```



## Authors

XU Xianghua <dayigu at gmail dot com>

Jan Drees <jdrees at mail dot uni-paderborn dot de>

Timothy-Edward-Kendon

YuyangL
