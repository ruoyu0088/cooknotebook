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


def solve(solver, variables, collector_name="First", monitors=None):
    if monitors is None:
        monitors = []
    solution = solver.Assignment()
    solution.Add(variables)
    collector = getattr(solver, collector_name + "SolutionCollector")(solution)
    phase = solver.Phase(variables, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
    if solver.Solve(phase, [collector] + monitors):
        return iter_solutions(collector)
    else:
        return ()


class LogMonitor(pywrapcp.SearchMonitor):
    def EnterSearch(self):
        print("EnterSearch")

    def RestartSearch(self):
        print("RestartSearch")

    def ExitSearch(self):
        print("ExitSearch")

    def BeginNextDecision(self, b):
        print("BeginNextDecision", b)

    def EndNextDecision(self, b, d):
        print("EndNextDecision", b, d)

    def ApplyDecision(self, d):
        print("ApplyDecision", d)

    def RefuteDecision(self, d):
        print("RefuteDecision", d)

    def AfterDecision(self, d, apply):
        print("AfterDecision", d, apply)

    def BeginFail(self):
        print("BeginFail")

    def EndFail(self):
        print("EndFail")

    def BeginInitialPropagation(self):
        print("BeginInitialPropagation")

    def EndInitialPropagation(self):
        print("EndInitialPropagation")

    def AcceptSolution(self):
        print("AcceptSolution")
        return super().AcceptSolution()

    def AtSolution(self):
        print("AtSolution")
        return super().AtSolution()

    def NoMoreSolutions(self):
        print("NoMoreSolutions")


class TreeMonitor(pywrapcp.SearchMonitor):
    def EnterSearch(self):
        self.from_node = []
        self.edge = []
        self.graph = []
        self.ignore_next_fail = False
        self.fail_count = 0

    def BeginNextDecision(self, b):
        node_text = str(b)
        node_text = node_text[node_text.index("("):][1:-1]
        if self.from_node and self.edge:
            self.graph.append([self.from_node[-1], self.edge[-1], node_text])
        self.from_node.append(node_text)

    def ApplyDecision(self, d):
        self.edge.append(str(d)[1:-1])

    def EndNextDecision(self, b, d):
        pass

    def RefuteDecision(self, d):
        edge = str(d)[1:-1]
        while self.edge[-1] != edge:
            self.edge.pop()
            self.from_node.pop()
        self.edge.pop()
        self.from_node.pop()
        self.edge.append("!" + edge)

    def AcceptSolution(self):
        self.ignore_next_fail = True
        return True

    def BeginFail(self):
        if not self.ignore_next_fail:
            self.fail_count += 1
            node_text = "Fail{}".format(self.fail_count)
            if self.from_node and self.edge:
                self.graph.append([self.from_node[-1], self.edge[-1], node_text])
            self.from_node.append(node_text)

        self.ignore_next_fail = False


jscode = """
require(['vis'], function(vis){
  var nodes = {{nodes}};
  var edges = {{edges}};
  var container = document.getElementById('{{uid}}');
  var data = {
    nodes: nodes,
    edges: edges
  };
  var options = {
    width: '{{width}}px',
    height: '{{height}}px',
    layout: {
        hierarchical: {
            direction: 'UD'
        }
    }
  };
  var network = new vis.Network(container, data, options);
});
"""

def display_graph(graph, height=500, width=600, label_width=1):
    from jinja2 import Template
    from IPython.display import display_html, display_javascript
    import uuid
    import json

    def get_label(node):
        if node.startswith("Fail"):
            return "Fail"
        elif label_width == 1:
            return node
        else:
            items = node.split(",")
            return "\n".join(",".join(items[i:i+label_width]).strip() for i in range(0, len(items), label_width))

    nodes = set()
    nodes_level = {graph[0][0]: 0}

    for start, edge, end in graph:
        nodes.add(start)
        nodes.add(end)
        nodes_level[end] = nodes_level[start] + 1

    nodes = list(nodes)
    nodes_dict = {node:i for i, node in enumerate(nodes)}

    nodes_json = [{"id": i, "label": get_label(node), "level": nodes_level[node], "shape": 'box'} for i, node in enumerate(nodes)]
    edges_json = [{"from": nodes_dict[start], "to": nodes_dict[end], "label":edge, "arrows":'to', "font": {"align": 'top'}}
                  for start, edge, end in graph]

    uid = str(uuid.uuid1()).replace("-", "")
    display_html('<div id="{}"></div>'.format(uid), raw=True)
    code = Template(jscode).render(nodes=json.dumps(nodes_json, indent=4),
                         edges=json.dumps(edges_json, indent=4),
                         uid=uid,
                         height=height,
                         width=width)
    display_javascript(code, raw=True)