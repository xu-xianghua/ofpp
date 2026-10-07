"""
postproc_parser.py

parser for OpenFoam postProcessing .dat files
"""
from __future__ import print_function

import numpy as np
from pathlib import Path
from typing import Tuple, List
from collections import defaultdict

def _split_line_to_vectors(line:str) -> List:
    """Split a line into entries, where an entry is either a scalar 'value' or a vector '(value...)'."""
    line = line.replace("\t", " ")
    line_split = []
    s = ""
    def _append_and_reset(s):
        s = s.strip(" \t\n")
        if len(s) > 0:
            line_split.append(s)
        return ""

    for a in line:
        if a == "(":
            s = _append_and_reset(s)
            s += a
        elif a == ")":
            s += a
            s = _append_and_reset(s)
        else:
            s += a
    _ = _append_and_reset(s)

    out = []
    for a in line_split:
        if a.startswith("("):
            out.append(a)
        else:
            out.extend(a.split(" "))
    return out


def _read_headers(line:str, sample_data:str) -> List:
    if "\t" in line:
        _headers = line.split("\t")
    else:
        _headers = line.split()
    _headers = [a.strip(" \n\t") for a in _headers]
    vector_count = sample_data.count("(")
    if vector_count == 0:
        return _headers
    # if vectors, add subscripts to headers
    else:
        sample_split = _split_line_to_vectors(sample_data)
        if len(sample_split) != len(_headers):
            print(sample_split, _headers)
            raise ValueError(f"Headers suggest {len(_headers)} values, but data shows {len(sample_split)} values.")
        headers = []
        for h, data in zip(_headers, sample_split):
            a = data.strip("(").strip(")").split(" ")
            if len(a) == 1:
                headers.append(h)
            elif len(a) > 1:
                for i in range(len(a)):
                    headers.append(f"{h}_{i}")
            else:
                raise ValueError(f"Unexpected value {a} when parsing headers.")
        return headers



def parse_postproc_matrix(path:Path) -> Tuple[np.ndarray, List, List]:
    """Read simple matrix format.

    For example, probes in post processing, where all the values are numeric. The values may be scalars or vectors.

    ```
    # comments
    # ...
    # Time Value1 Value2 ...
    t_0    v1_0   v2_0   ...
    t_1    v1_1   v2_1   ...
    ```
    """

    data = []
    comments = []
    headers = None
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                comments.append(line.strip("# "))
            else:
                # expect the last comment line to be labels
                if not headers:
                    headers = _read_headers(comments.pop(-1), sample_data=line)

                line = line.replace("(", " ").replace(")", " ")
                line_split = line.split()
                row = []
                for v in line_split:
                    if v == "N/A":
                        row.append(np.nan)
                    else:
                        row.append(float(v))
                data.append(row)

    data = np.array(data)
    return data, headers, comments


def parse_postproc_matrix_with_patch(path:Path):
    """Read post processing .dat files that contains patches."""
    data_all = defaultdict(list)

    data = []
    comments = []
    headers = None
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                comments.append(line.strip("# "))
            else:
                # expect the last comment line to be labels
                if not headers:
                    headers = _read_headers(comments[-1], sample_data=line)

                line = line.replace("(", " ").replace(")", " ")
                line_split = line.split()
                row = []
                for i, v in enumerate(line_split):
                    if v == "N/A":
                        row.append(np.nan)
                    elif v[0].isalpha():
                        name = v # patch name
                        name_idx = i
                    else:
                        row.append(float(v))
                data_all[name].append(row)
                # data.append(row)
    data = {}
    for key, value in data_all.items():
        data[key] = np.array(value)
    headers.pop(name_idx)
    return data, headers, comments


def parse_postproc_time_series(path:Path, filename:str, type:int = 0) -> Tuple[np.ndarray|dict, List, List]:
    """Read a postProcessing time series saved under the same folder.
    
    For example, probes/0/a.dat, probes/20/a.dat ...

    - path: path to the folder containing the time series. In the example, path would be /path-to/postProcessing/probes/
    - filename: the filename of the .dat file. In the example, this would be a.dat.
    - type: 0 -> simple matrix; 1 -> with patches
    """

    if type == 0:
        data = []
    elif type == 1:
        data = defaultdict(list)
    else:
        raise ValueError(f"Type {type} not found.")
    comments = []
    headers = None
    path = Path(path)
    time = [p.name for p in path.iterdir()]
    time_float = [float(a) for a in time]
    idx = np.argsort(time_float)
    # Iterate in sequence
    for i in idx:
        folder = path / time[i]

        if type == 0:
            _data, _headers, _comments = parse_postproc_matrix(folder / filename)
            comments.append(_comments)
            if headers is None:
                headers = _headers
            elif headers != _headers:
                raise ValueError(f"The files in the time series have different headers.")
            data.append(_data)
        elif type == 1:
            _data, _headers, _comments = parse_postproc_matrix_with_patch(folder / filename)
            comments.append(_comments)
            if headers is None:
                headers = _headers
            elif headers != _headers:
                raise ValueError(f"The files in the time series have different headers.")
            for k,v in _data.items():
                data[k].append(v)

    if type == 0:
        data = np.concatenate(data, axis=0)
    elif type == 1:
        for k in data.keys():
            data[k] = np.concatenate(data[k], axis=0)

    return data, headers, comments
