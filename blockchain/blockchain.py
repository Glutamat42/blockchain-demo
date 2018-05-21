import hashlib
import json
import time
import requests
from uuid import uuid4
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create genesis block
        # self.new_block(previous_hash=1, proof=100)

        # load blockchain from hdd
        self.loadExistingChain()
        # get addresses of many other nodes
        self.findNodes()
        # update own chain
        self.resolve_conflicts()

    def loadExistingChain(self):
        """
        load chain from file system
        """

        # TODO
        self.chain.append({
            'index': 1,
            'timestamp': 1526928965.244928,
            'transactions': [],
            'proof': 1,
            'previous_hash': '1',
        })

    def findNodes(self):
        """
        uses different algorithms to find other nodes
        """

        # TODO: add ips of nodes sending data to our node

        # TODO
        self.nodes.add('127.0.0.1:5001')
        self.nodes.add('127.0.0.1:5000')

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # reset current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        newTx = {
            'txid': str(uuid4()).replace('-', ''),
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }

        self.current_transactions.append(newTx)

        if sender is not '0':
            self.spreadTransactions([newTx])

        return self.last_block['index'] + 1

    def spreadTransactions(self, transactions):
        """
        broadcasts new transactions to the network
        :param transactions: <array> Transactions
        """
        for node in self.nodes:
            try:
                requests.post(f'http://{node}/transactions/add', json={'transactions': json.dumps(transactions)}, timeout=1.0)
            except:
                print(f'could not reach host {node}')

    def spreadBlock(self, block):
        """
        broadcasts the latest block to the network
        :param block: <dict> one block
        """
        for node in self.nodes:
            try:
                requests.post(f'http://{node}/block/add', json={'block': json.dumps(block)}, timeout=1.0)
            except:
                print(f'could not reach host {node}')

    def receivedBlock(self, block):
        """
        checks wether a received block is valid and not already in the nodes blockchain

        :param block: <dict> Block
        :return: Wether the block was added or not
        """

        newBlock = json.loads(block)
        if self.hash(newBlock) is not self.hash(self.chain[-1]):
            if self.valid_chain(self.chain + [newBlock]):
                self.chain.append(newBlock)
                self.spreadBlock(newBlock)
                return True
        return False

    def receivedTransactions(self, transactions):
        """
        Receives a list of transactions of another node.
        If the transaction is not already in a block it will be added to own transactions list

        :param transactions: <array> Transactions
        """

        # list of not already known transactions -> broadcast to network
        unknownTransactions = []

        receivedTransactions = json.loads(transactions)
        for newTransaction in receivedTransactions:
            txIsNew = True
            for block in self.chain:
                for tx in block['transactions']:
                    if newTransaction['txid'] is tx['txid']:
                        txIsNew = False
            if txIsNew:
                self.current_transactions.append(newTransaction)
                unknownTransactions.append(newTransaction)

        if len(unknownTransactions) > 0:
            self.spreadTransactions(unknownTransactions)

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # verify hash of the block
            if block['previous_hash'] != self.hash(last_block):
                return False

            # verify the proof of work
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain', timeout=1.0)

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # check if chain is longer and valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except:
                print(f'could not reach host {node}')

        # replace our chain if we discovered a longer one
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]
