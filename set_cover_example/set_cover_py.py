#!/usr/bin/env python3
from sys import stderr
import os
import argparse
from pathlib import Path

#import numpy as np
#import scipy.sparse as sp

import gurobipy as gp
from gurobipy import GRB

def to_bool(x):
    if x > 1/2:
        return True
    if x < -1/2:
        return True
    return False

""" general supporting data (the various programs will resort only on parts of these):
    num_timeslots = tmax (int)
    examIDs (set)
    studIDs (set)
    studs_enrolled_to_exam (Dict<Set>)
    num_studs_enrolled_to_exam (Dict<int>)
    timeslot_of_exam (Dict<int>)
    exams_at_timeslot (List<List>)
"""

def conflicting(examA, examB):
    #print(f"called conflicting({examA=}, {examB=})", file=stderr)
    #print(f"{studs_enrolled_to_exam=}", file=stderr)
    return 0 < len(studs_enrolled_to_exam[examA] & studs_enrolled_to_exam[examB])
            
def check_feasible():
    for t in range(1, 1+num_timeslots):
        activity = { s:None for s in studIDs}
        for e in exams_at_timeslot[t]:
            for s in studs_enrolled_to_exam[e]:
                if activity[s] is None:
                    activity[s] = e
                else:
                    print(f"Ahi: the solution proposed is not feasible since at timeslot {t} the student {s} should attend both the exam {activity[s]} and the exam {e}!", file=stderr)
                    return False
    return True

            
def penality():
    p = 0.0
    students_active_in_timewind = [ set({}), set({}), set({}), set({}), set({}), set({}) ]
    for t in range(1, 1+num_timeslots):
        students_active_in_timewind[t % 6] = set({})
        activity = { s:None for s in studIDs}
        for e in exams_at_timeslot[t]:
            for s in studs_enrolled_to_exam[e]:
                if activity[s] is None:
                    activity[s] = e
                    students_active_in_timewind[t % 6].add(s)
                else:
                    print(f"Ahi: the solution proposed is not feasible since at timeslot {t} the student {s} should attend both the exam {activity[s]} and the exam {e}!", file=stderr)
                    exit(1)
            for time_shift in range(1, 6):
                p += 2**(5 - time_shift) * len(studs_enrolled_to_exam[e].intersection( students_active_in_timewind[(t - time_shift)% 6]) ) / len(studIDs)
    return p
            


if __name__ == "__main__":
    # Instantiate the parser
    parser = argparse.ArgumentParser(description="This program yields an optimal solution for the instance contained into the input data file (.stu file versus .slo file). Please, provide the input data files.", epilog="""-------------------""")

    # Required positional arguments
    parser.add_argument("slo_filename", type=str,
                        help="[string] first required positional argument - the filename of the file containing the length of the examination period.")
    parser.add_argument("stu_filename", type=str,
                        help="[string] second required positional argument - the filename of the file containing the list of the enrollments (i.e., ID_student - ID_exam pairs).")

    args = parser.parse_args()

    FILE_SLO = os.path.join(os.getcwd(), args.slo_filename)
    if not os.path.exists(FILE_SLO):
        if slo_filename[-4] != ".":
            if not os.path.exists(FILE_SLO+".slo"):
                print(f"Error: I could not find the file:\n    {FILE_SLO}\nThis file is needed (launch this script with the -h flag to know more about its usage!).")
                exit(1)
            else:
               FILE_SLO = FILE_SLO+".slo"
    if not os.path.isfile(FILE_SLO):
        print(f"Error: the following is not the path of a file:\n    {FILE_SLO}\nthis seems to be the path of a directory!).")
        exit(1)

    FILE_STU = os.path.join(os.getcwd(), args.stu_filename)
    if not os.path.exists(FILE_STU):
        if stu_filename[-4] != ".":
            if not os.path.exists(FILE_STU+".stu"):
                print(f"Error: I could not find the file:\n    {FILE_STU}\nThis file is needed (launch this script with the -h flag to know more about its usage!).")
                exit(1)
            else:
               FILE_STU = FILE_STU+".stu"
    if not os.path.isfile(FILE_STU):
        print(f"Error: the following is not the path of a file:\n    {FILE_STU}\nthis seems to be the path of a directory!).")
        exit(1)


    # BEGIN: READING THE CONTENT OF THE REQUIRED FILES:
    # required filenames: FILE_SLO, FILE_STU, FILE_EXM, FILE_SOL

    examIDs = set({})
    studIDs = set({})
    
    with open(FILE_SLO) as file_slo:
        num_timeslots = tmax = int(file_slo.readline())

    with open(FILE_STU) as file_stu:
        stu_lines = file_stu.readlines()
        #print(f"{stu_lines=}", file=stderr)
        studs_enrolled_to_exam = {}
        for line in stu_lines:
            ID_stud, ID_exam = line.strip().split()
            ID_exam = int(ID_exam)
            examIDs.add(ID_exam)
            studIDs.add(ID_stud)
            if ID_exam in studs_enrolled_to_exam:
                if ID_stud in studs_enrolled_to_exam[ID_exam]:
                    print(f"WARNING: double registration of student {ID_stud} to exam {ID_exam}!", file=stderr)
                else:
                    studs_enrolled_to_exam[ID_exam].add(ID_stud)
            else:
                studs_enrolled_to_exam[ID_exam] = {ID_stud}
    print(f"{examIDs=}", file=stderr)
    print(f"{studIDs=}", file=stderr)
    print(f"{studs_enrolled_to_exam=}", file=stderr)
    num_exams = len(studs_enrolled_to_exam)
    # END: READING THE CONTENT OF THE REQUIRED FILES

    # BEGIN OF THE SMALL LOGIC SECTION:
    T = list(range(1, 1+num_timeslots)) # la lista dei timeslots
    E = list(range(1, 1+num_exams)) # la lista degli esami
    D = list(range(1, 6)) # la lista delle distanze che comportano pagamento di penality

    # Create optimization model:
    m = gp.Model('schedule_exams')

    # Create variables:
    # the true decision variables:
    x = m.addVars( E, T, vtype=GRB.BINARY, name="x")
    # x[e, t] = 1 if exam e is scheduled in timeslot t

    # auxiliary variables:
    p = m.addVars( E, E, name="p")
    # p[i, j] = the penality incurred over the pair of exams i and j

    # Constraints:
    # feasibility (only the true decision variables are needed):
    # every exam goes is assigned precisely one timeslot:
    m.addConstrs((x.sum(e,'*') == 1 for e in E), "precisely_one_timeslot_to_exam_")
    
    # no two conflicting exams into a same timeslot:
    for i in E:
      for j in E:
        if i < j and conflicting(i, j):
            for t in T:
                m.addConstr(x[i,t] + x[j,t] <= 1, f"conflict_{i=}_{j=}_{t=}")
    m.update()
    # m.addConstrs((x.sum('*',t) <= 1 for t in T), "conflict_at_time_")

    # partial definition of the auxiliary variables p:
    def cost(shift):
        assert 1 <= shift <= 5
        return 2**(5-shift)
    
    for shift in range(1, 6):
        for i in E:
          for j in E:
            if i < j:  
                for tt in T:
                    if tt + shift <= num_timeslots:
                        m.addConstr(p[i,j] >= cost(shift) * x[i,tt]  + cost(shift) * x[j, tt + shift]  - cost(shift), f"part_def_var_p_{i}_{j}A")
                        m.addConstr(p[i,j] >= cost(shift) * x[i,tt + shift]  + cost(shift) * x[j, tt]  - cost(shift), f"part_def_var_p_{i}_{j}B")
    
    # Set objective function
    m.setObjective(gp.quicksum(p), GRB.MINIMIZE)

    # Compute optimal solution
    m.optimize()

    # how to access the variable values:
    #for v in m.getVars():
    #    print(f"{v.VarName} = {v.X}")

    timeslot_of_exam = [None] * (num_exams +1)
    for i in E:
        for tt in T:
            if to_bool(x[i,tt].X):
                timeslot_of_exam[i] = tt
                continue
    print(f"timeslot_of_exam={timeslot_of_exam[1:]}", file=stderr)    

    exams_at_timeslot = [ [] for _ in range(num_timeslots +1) ]
    for ID_exam in range(1, 1+num_exams):
        exams_at_timeslot[ timeslot_of_exam[ID_exam] ].append(ID_exam)
    print(f"exams_at_timeslot={exams_at_timeslot[1:]}", file=stderr)

    print(f"{check_feasible()=}")
    print(f"{penality()=}")
    
