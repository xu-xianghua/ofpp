"""
field_parser.py
parser for field data

"""
from __future__  import print_function

import re
import os
import io
import numpy as np


def parse_field_all(fn):
    """
    parse internal field, extract data to numpy.array
    :param fn: file name
    :return: numpy array of internal field and boundary
    """
    if not os.path.exists(fn):
        print("Can not open file " + fn)
        return None
    with io.open(fn, encoding="utf-8") as f:
        content = f.readlines()
        return parse_internal_field_content(content), parse_boundary_content(content)


def parse_internal_field(fn):
    """
    parse internal field, extract data to numpy.array
    :param fn: file name
    :return: numpy array of internal field
    """
    if not os.path.exists(fn):
        print("Can not open file " + fn)
        return None
    with io.open(fn, encoding="utf-8") as f:
        content = f.readlines()
        return parse_internal_field_content(content)


def parse_internal_field_content(content):
    """
    parse internal field from content
    :param content: contents of lines
    :return: numpy array of internal field
    """
    for ln, lc in enumerate(content):
        if lc.startswith('internalField'):
            if 'nonuniform' in lc:
                if 'vector' in lc or 'tensor' in lc:
                    return parse_data_nonuniform(content, ln, True)
                return parse_data_nonuniform(content, ln, False)
            elif 'uniform' in lc:
                return parse_data_uniform(content[ln])
            break
    return None


def parse_boundary_field(fn):
    """
    parse internal field, extract data to numpy.array
    :param fn: file name
    :return: numpy array of boundary field
    """
    if not os.path.exists(fn):
        print("Can not open file " + fn)
        return None
    with io.open(fn, encoding="utf-8") as f:
        content = f.readlines()
        return parse_boundary_content(content)


def parse_boundary_content(content):
    """
    parse each boundary from boundaryField
    :param content:
    :return:
    """
    data = {}
    bd = split_boundary_content(content)
    for boundary, (n1, n2) in bd.items():
        pd = {}
        n = n1
        while True:
            lc = content[n]
            if 'nonuniform' in lc:
                if 'vector' in lc or 'tensor' in lc:
                    v = parse_data_nonuniform(content, n, True)
                else:
                    v = parse_data_nonuniform(content, n, False)
                pd[lc.split()[0]] = v
                n += len(v) + 4
                continue
            elif 'uniform' in lc:
                pd[lc.split()[0]] = parse_data_uniform(content[n])
            n += 1
            if n > n2:
                break
        data[boundary] = pd
    return data


def parse_data_uniform(line):
    """
    parse uniform data from a line
    :param line: a line include uniform data, eg. "value           uniform (0 0 0);"
    :return: data
    """
    p = re.compile('uniform\s*\((.*)\)')
    ps = p.search(line)
    if ps is not None:
        return np.loadtxt(io.StringIO(ps.group(1)))
    p = re.compile('uniform\s*(.*);')
    ps = p.search(line)
    if ps is not None:
        try:
            v = float(ps.group(1))
            return v
        except:
            return None
    else:
        return None

def parse_data_nonuniform(content, n, is_vector):
    """
    parse uniform data from a line
    :param content: data content
    :param n: line number
    :param is_vector: data is vector or not
    :return: data
    """
    num = int(content[n + 1])
    if is_vector:
        data = np.loadtxt(io.StringIO('\n'.join([s[1:-2] for s in content[n + 3:n + 3 + num]])))
    else:
        data = np.loadtxt(io.StringIO('\n'.join(content[n + 3:n + 3 + num])))
    return data


def split_boundary_content(content):
    """
    split each boundary from boundaryField
    :param content:
    :return: boundary and its content range
    """
    bd = {}
    n = 0
    in_boundary_field = False
    in_patch_field = False
    current_path = ''
    while True:
        lc = content[n]
        if lc.startswith('boundaryField'):
            in_boundary_field = True
            if content[n+1].startswith('{'):
                n += 2
                continue
            elif content[n+1].strip() == '' and content[n+2].startswith('{'):
                n += 3
                continue
            else:
                print('no { after boundaryField')
                break
        if in_boundary_field:
            if lc.startswith('}'):
                break
            if in_patch_field:
                if lc.strip() == '}':
                    bd[current_path][1] = n-1
                    in_patch_field = False
                    current_path = ''
                n += 1
                continue
            if lc.strip() == '':
                n += 1
                continue
            current_path = lc.strip()
            if content[n+1].strip() == '{':
                n += 2
            elif content[n+1].strip() == '' and content[n+2].strip() == '{':
                n += 3
            else:
                print('no { after boundary patch')
                break
            in_patch_field = True
            bd[current_path] = [n,n]
            continue
        n += 1
        if n > len(content):
            if in_boundary_field:
                print('error, boundaryField not end with }')
            break

    return bd

