#!/usr/bin/env python3
from sys import stderr
import os

import gurobipy as gp
from gurobipy import GRB

"""
   general supporting data (the various programs will resort only on parts of these):
  INPUT:
    n = number of elements to be covered
    m = number of available sets
    ele_covered_by (List<int>)
   Note:
    - the elements in the groundset to be covered are labelled with the natural numberes from 0 to n-1
    - the sets are labelled with the natural numberes from 0 to m-1
"""

n = 6
m = 5
ele_covered_by = [
    [0, 1, 3],
    [0, 2, 5],
    [1, 3, 4],
    [2, 3, 5],
    [0, 5]
]


V = list(range(n)) # list containing the names of the nodes (elements of the groundset to be covered) 
S = list(range(m)) # list containing the names of the sets available

# Create optimization model:
m = gp.Model('set_cover')

# Create variables:
x = m.addVars( S, vtype=GRB.BINARY, name="x")
# x[s] = 1 if the set s is selected, otherwise x[s] = 0 

# Now we should define the constraints ...

    # every element must be contained in at least one of the selected sets
    # I find it slightly difficult to express this:
    # sum(x_s : s in S such that s contains v)  >= 1   for every v in V           
