#!/usr/bin/env python3

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


if __name__ == "__main__":
    pass

