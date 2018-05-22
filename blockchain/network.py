import json
import requests
from urllib.parse import urlparse

class Network:
    def __init__(self):
        self.nodes = set()
        self.findNodes()

    def findNodes(self):
        """
        uses different algorithms to find other nodes
        """

        # TODO: add ips of nodes sending data to our node

        # TODO
        self.nodes.add('127.0.0.1:5001')
        self.nodes.add('127.0.0.1:5000')

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def postToEveryNode(self, url, jsonKey, jsonData):
        """
        send data to all nodes

        :param url: <str> eg. transactions/add (without leading '/')
        :param json: <dict> data that should be send
        :return:
        """
        for node in self.nodes:
            try:
                requests.post(f'http://{node}/{url}', json={jsonKey: json.dumps(jsonData)}, timeout=1.5)
            except requests.ReadTimeout:
                print(f'could not reach host {node}')
            except requests.ConnectionError:
                print(f'could not reach host {node}')

