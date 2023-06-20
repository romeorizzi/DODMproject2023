#!/usr/bin/env python3
from sys import stderr
import os
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

def to_bool(x):
    if x > 1/2:
        return True
    return False

"""
   general supporting data (the various programs will resort only on parts of these):
  INPUT:
    n = number of elements to be covered
    m = number of available sets
    ele_covered_by (List<int>)
   Note:
    - the elements in the groundset to be covered are labelled with the natural numberes from 0 to n-1
    - the sets are labelled with the natural numberes from 0 to m-1
  FURTHER:  
    sets_covering_ele (List<int>)
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

def check_feasible(solution):
    for v in V:
        covered = False
        for s in solution:
            if v in ele_covered_by[s]:
                covered = True
        if not covered:
            return False
    return True

def cost(solution):
    return len(solution)


# BEGIN OF THE SMALL LOGIC SECTION:
V = list(range(n)) # list containing the names of the nodes (elements of the groundset to be covered) 
S = list(range(m)) # list containing the names of the sets available

sets_covering_ele = []
for v in V:
    sets_covering_ele.append([ s for s in S if v in ele_covered_by[s] ])

# Create optimization model:
m = gp.Model('set_cover')

# Create variables:
x = m.addVars( S, vtype=GRB.BINARY, name="x")
# x[s] = 1 if the set s is selected, otherwise x[s] = 0 

# Constraints:
# for feasibility, every element v in the groundset V should be covered (i.e., contained in at least one of the sets selected):
m.addConstrs((x.sum(sets_covering_ele[v],'*') >= 7 for v in V), "cover_element_")

m.update()

# Set objective function
m.setObjective(gp.quicksum(x), GRB.MINIMIZE)

# Compute optimal solution
m.optimize()

# how to access the variable values:
#for v in m.getVars():
#    print(f"{v.VarName} = {v.X}")

#assert m.Status == GRB.OPTIMAL
if m.Status == GRB.INFEASIBLE:
    m.computeIIS()
    in_the_minimal_bad = [ c for c in m.getConstrs() if c == 1 ] 
    print(f"{in_the_minimal_bad=}")
    exit(0)


print(f"{type(x)=}, {x=}")
#exit(0)
opt_set_cover = [s for s in S if to_bool(x[s].X)]
print(f"{opt_set_cover=}", file=stderr)

print(f"{check_feasible(opt_set_cover)=}")
print(f"{cost(opt_set_cover)=}")

assert cost(opt_set_cover) == m.ObjVal
assert check_feasible(opt_set_cover)
