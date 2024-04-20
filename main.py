import csv
import subprocess
import random

class Node:
    def __init__(self, id, x, y, type="traffic_light"):
        self.id = id # string
        self.x = x # float (meters)
        self.y = y # float (meters)
        self.type = type # predefined string (traffic_light, priority, stop, traffic_sign, right_before_left, unregulated)

    def to_xml(self):
        return f'    <node id="{self.id}" x="{self.x}" y="{self.y}" type="{self.type}"/>\n'

# Represents a road segment
class Edge:
    def __init__(self, id, from_node, to_node, priority=2, num_lanes=2, speed=14.0):
        self.id = id # string
        self.from_node = from_node # node object
        self.to_node = to_node # node object
        self.priority = priority # integer
        self.num_lanes = num_lanes # integer
        self.speed = speed # float

    def to_xml(self):
        return f'    <edge id="{self.id}" from="{self.from_node.id}" to="{self.to_node.id}" priority="{self.priority}" numLanes="{self.num_lanes}" speed="{self.speed}"/>\n'

class Network:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges.append(edge)

    def create_nod_xml(self, filename="nodes.nod.xml"):
        print("Creating nodes.nod.xml...")
        with open(filename, "w") as f:
            f.write("<nodes>\n")
            for node in self.nodes:
                f.write(node.to_xml())
            f.write("</nodes>\n")

    def create_edg_xml(self, filename="edges.edg.xml"):
        print("Creating edges.edg.xml...")
        with open(filename, "w") as f:
            f.write("<edges>\n")
            for edge in self.edges:
                f.write(edge.to_xml())
            f.write("</edges>\n")

    def convert_net_xml(self, filename="network.net.xml"):
        self.create_nod_xml()
        self.create_edg_xml()
        subprocess.run(f"netconvert --node-files=nodes.nod.xml --edge-files=edges.edg.xml --output-file={filename}", shell=True)

def create_config_file():
    # manually create a SUMO configuration file
    config_content = """<configuration>
    <input>
        <net-file value="network.net.xml"/>
        <route-files value="routes.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="86400"/>
    </time>
</configuration>"""

    with open("config.sumocfg", "w") as config_file:
        config_file.write(config_content)

def read_csv_and_build_network(csv_path):
    network = Network()
    nodes_dict = {}

    # Define maximum bounds
    max_x, max_y = 5000, 5000

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            edge_ids_str = row['Edges'].strip("[]")
            if edge_ids_str:
                edge_ids = [id.strip() for id in edge_ids_str.split(",")]
                if len(edge_ids) >= 2:
                    from_node_id, to_node_id = edge_ids[0], edge_ids[1]

                    for node_id in [from_node_id, to_node_id]:
                        if node_id not in nodes_dict:
                            x = random.randint(0, max_x)
                            y = random.randint(0, max_y)
                            node = Node(node_id, x, y)
                            nodes_dict[node_id] = node
                            network.add_node(node)

                    # Create the initial direction
                    edge = Edge(row['Signal ID'], nodes_dict[from_node_id], nodes_dict[to_node_id])
                    network.add_edge(edge)

                    # Create the second direction
                    rev_edge_id = row['Signal ID'] + "_rev"
                    rev_edge = Edge(rev_edge_id, nodes_dict[to_node_id], nodes_dict[from_node_id])
                    network.add_edge(rev_edge)

    network.create_nod_xml()
    network.create_edg_xml()
    network.convert_net_xml()



csv_path = "signalData - Sheet2.csv"
read_csv_and_build_network(csv_path)

subprocess.run("randomTrips.py -n network.net.xml -e 600 -o unconvtrips.trips.xml", shell=True)
subprocess.run("duarouter -n network.net.xml --route-files unconvtrips.trips.xml -o routes.rou.xml --ignore-errors",
               shell=True)

print("Creating SUMO configuration file...")
create_config_file()

# Run GUI with the generated network
subprocess.run("sumo-gui -c config.sumocfg --tripinfo-output", shell=True)