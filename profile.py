"""This profile sets up a network of compute nodes connected to a NFS server which in turn mounts a dataset

"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Only Ubuntu images supported.
imageList = [
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD', 'UBUNTU 16.04'),
]

trueFalse = [
    ('False', 'False'),
    ('True', 'True'),
]

# Do not change these unless you change the setup scripts too.
nfsServerName = "nfs"
nfsLanName    = "nfsLan"
nfsDirectory  = "/nfs"

# Number of NFS clients (there is always a server)
pc.defineParameter("clientCount", "Number of Compute Nodes (1-4)",
                   portal.ParameterType.INTEGER, 2)

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList)

pc.defineParameter("datasetURN",  "Dataset URN",
                   portal.ParameterType.STRING, "",
                   longDescription="Provide the URN of the Dataset you want to use in this experiment")

pc.defineParameter("datasetReadOnly", "Mount Dataset Readonly",
                   portal.ParameterType.STRING,
                   trueFalse[0], trueFalse)


pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.STRING, "",
                   longDescription="Specify a physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

pc.defineParameter("localStorage", "Extra local storage in GB",
                   portal.ParameterType.INTEGER, 0)


pc.defineParameter("node1",  "Node 1 URN",
                   portal.ParameterType.STRING, "",
                   longDescription="Provide the URN of node1, if available")

pc.defineParameter("node2",  "Node 2 URN",
                   portal.ParameterType.STRING, "",
                   longDescription="Provide the URN of node2, if available")

pc.defineParameter("node3",  "Node 3 URN",
                   portal.ParameterType.STRING, "",
                   longDescription="Provide the URN of node3, if available")

pc.defineParameter("node4",  "Node 4 URN",
                   portal.ParameterType.STRING, "",
                   longDescription="Provide the URN of node4, if available")


# Always need this when using parameters
params = pc.bindParameters()

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort       = True
nfsLan.vlan_tagging      = True
nfsLan.link_multiplexing = True

if params.datasetURN != "":

	# The NFS server.
	nfsServer = request.RawPC(nfsServerName)
	nfsServer.disk_image = params.osImage
	# Attach server to lan.
	nfsLan.addInterface(nfsServer.addInterface())
	# Initialization script for the server
	nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))

	# Special node that represents the ISCSI device where the dataset resides
	dsnode = request.RemoteBlockstore("dsnode", nfsDirectory)
	dsnode.dataset = params.datasetURN
	if params.datasetReadOnly == "True":
		dsnode.readonly = True
	else:
		dsnode.readonly = False
	# Link between the nfsServer and the ISCSI device that holds the dataset
	dslink = request.Link("dslink")
	dslink.addInterface(dsnode.interface)
	dslink.addInterface(nfsServer.addInterface())
	# Special attributes for this link that we must use.
	dslink.best_effort = True
	dslink.vlan_tagging = True
	dslink.link_multiplexing = True
	pass


# The NFS clients, also attached to the NFS lan.
for i in range(1, params.clientCount+1):
    node = request.RawPC("node%d" % i)
    node.disk_image = params.osImage
    # Initialization script for the clients
    nfsLan.addInterface(node.addInterface())
    if params.datasetURN != "":
    	node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))
        pass
    if params.phystype != "":
        node.hardware_type = params.phystype
        pass
    if params["node"+str(i)] != "":
	node.disk_image=params["node"+str(i)]
        pass
    if params.localStorage != 0:
	bsName="bs"+str(i)
        bs = node.Blockstore(bsName, "/mydata")
        bs.size=str(params.localStorage)+"GB"
    pass


# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
