from ortools.constraint_solver import pywrapcp


def SolutionCollector__len__(self):
    return self.SolutionCount()

def SolutionCollector__getitem__(self, index):
    if index < len(self):
        return self.Solution(index)
    else:
        raise IndexError("index out of range {} of {}".format(index, len(self)))

def IntContainer__getitem__(self, index):
    if index < len(self):
        return self.Element(index)
    else:
        raise IndexError("index out of range {} of {}".format(index, len(self)))


pywrapcp.SolutionCollector.__len__ = lambda self: self.SolutionCount()
pywrapcp.SolutionCollector.__getitem__ = SolutionCollector__getitem__

pywrapcp.Assignment.intvars = property(lambda self: self.IntVarContainer())
pywrapcp.IntContainer.__len__ = lambda self: self.Size()
pywrapcp.IntContainer.__getitem__ = IntContainer__getitem__
pywrapcp.IntVarElement.name = property(lambda self: self.Var().Name())
pywrapcp.IntVarElement.value = property(lambda self: self.Value())


def iter_solutions(collector):
    for assignment in collector:
        yield [(el.name, el.value) for el in assignment.intvars]


def solve(solver, variables, collector_name="First"):
    solution = solver.Assignment()
    solution.Add(variables)
    collector = getattr(solver, collector_name + "SolutionCollector")(solution)
    phase = solver.Phase(variables, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
    if solver.Solve(phase, [collector]):
        return iter_solutions(collector)
    else:
        return ()