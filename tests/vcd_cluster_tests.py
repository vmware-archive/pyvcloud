from nose.tools import with_setup
from pyvcloud.vcd.cluster import Cluster
from pyvcloud.vcd.client import Client
from testconfig import config

class cred:
	def __init__(self, user, org, password):
		self.user = user
		self.org = org
		self.password = password

class TestVCDCluster:

	def __init__(self):
		host = config['vcloud']['uri']
		version = '29.0'
		verify = config['vcloud']['verify']
		self.client = Client(uri=host, api_version= version, verify_ssl_certs=verify)
		self.client.set_credentials(cred(config['vcloud']['admin'], \
			config['vcloud']['au'], config['vcloud']['Admin!23']))
		self.cluster= Cluster(self.client)

	def listClus(self):
		assert self.cluster.get_clusters()

	def createClus(self):
		assert self.cluster.create_cluster('au-vdc', 'TestbedPG', 'test', node_count=2)


def test1(): 
	TestVCDCluster().listClus()


def test2(): 
	TestVCDCluster().createClus()
