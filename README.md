# Ofpp
Ofpp stands for OpenFOAM Python Parser. It is a simple Python library for parsing data in OpenFOAM output files to Numpy array.

## Installation

The simplest way: download the source code and add Ofpp directory to your Python path.

Or install with setup.py by:

```shell
python setup.py install
```

The depended package if Ofpp is Numpy.

## Usage

```python
import Ofpp
V = Ofpp.parse_internal_field('0/V')
wb01 = Ofpp.parse_boundary_field('0.1/alpha.water')
U02,Ub02 = Ofpp.parse_field_all('0.2/U')
```

The data of internal field is Numpy.array, and data of boundary is dictionary with boundary name as keys and Numpy.array as values.

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

Firstly, using function `parse_internal_field` parse '0/V' to get cell volume data,

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

Parse alpha.water of all time step, and calculate water volume of each time to check mass ballance: 

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

Parse velocity field, which is vector field. And calculate the velocity magnitude,

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

Boundary data parsed by Ofpp is a dictionary because there are usualy more than one boundary entities.  Its kes are boundary names and values are also dictionaries.

```python
>>> b01=Ofpp.parse_boundary_field('0.1/alpha.water')
>>> b01.keys()
dict_keys(['rightWall', 'atmosphere', 'leftWall', 'lowerWall', 'defaultFaces'])
>>> b01['atmosphere'].keys()
dict_keys(['inletValue', 'value'])
>>> b01['atmosphere']['inletValue']
0.0
>>> b01['atmosphere']['value'].shape
(46,)
>>> b01['atmosphere']['value']
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



## TODO

-  mesh data parser and mesh manipulation utilities

## Author

XU Xianghua <dayigu at gmail dot com>