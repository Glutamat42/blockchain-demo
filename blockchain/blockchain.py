import hashlib
import json
import requests
from uuid import uuid4
from network import Network
from block import Block


class Blockchain(object):
    def __init__(self):
        # TODO load on startup
        # generate unique node address
        self.node_identifier = str(uuid4()).replace('-', '')

        self.chain = []
        self.nodes = Network()

        # load blockchain from hdd
        self.loadExistingChain()

        self.nextBlock = Block(self.hash(self.last_block))

        # update own chain
        print('get latest chain from other nodes')
        self.resolve_conflicts()

    def loadExistingChain(self):
        """
        load chain from file system
        """

        # TODO
        newBlock = Block('1')
        newBlock.initExisting([], 1, 1526928965.244928)
        self.chain.append(newBlock)

    def new_block(self, proof):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        self.nextBlock.nonce = proof
        self.chain.append(self.nextBlock)
        self.nextBlock = Block(self.hash(self.nextBlock))

        return self.last_block

    def spreadTransactions(self, transactions):
        """
        broadcasts new transactions to the network
        :param transactions: <array> Transactions
        """
        self.nodes.postToEveryNode('transaction/add', 'transactions', transactions)

    def spreadBlock(self, block):
        """
        broadcasts the latest block to the network
        :param block: <dict> one block
        """
        self.nodes.postToEveryNode('block/add', 'block', block.getBlockAsJson())

    def receivedBlock(self, block):
        """
        checks wether a received block is valid and not already in the nodes blockchain

        :param block: <dict> Block
        :return: Wether the block was added or not
        """

        jsonBlock = json.loads(block)
        newBlock = Block(jsonBlock['previous_hash'])
        newBlock.initExisting(jsonBlock['transactions'], jsonBlock['nonce'], jsonBlock['timestamp'])
        if self.hash(newBlock) is not self.hash(self.chain[-1]):
            if self.valid_chain(self.chain + [newBlock]):
                self.chain.append(newBlock)
                self.spreadBlock(newBlock)
                return True
        return False

    def newTransaction(self, sender, recipient, amount):
        txid = self.nextBlock.new_transaction(sender, recipient, amount)
        if sender is not '0':
            self.spreadTransactions(self.nextBlock.getTxById(txid))
        return txid

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
                for tx in block.transactions:
                    if newTransaction['txid'] is tx['txid']:
                        txIsNew = False
            if txIsNew:
                self.nextBlock.transactions.append(newTransaction)
                unknownTransactions.append(newTransaction)

        if len(unknownTransactions) > 0:
            self.spreadTransactions(unknownTransactions)

    def proof_of_work(self, block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(block, proof) is False:
            proof += 1

        return proof

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
            if block.prevHash != self.hash(last_block):
                return False

            # verify the proof of work
            if not self.valid_proof(block, block.nonce):
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

        neighbours = self.nodes.nodes
        new_chain = None

        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain', timeout=1.5)

                if response.status_code == 200:
                    length = response.json()['length']
                    chainJson = response.json()['chain']
                    # convert json
                    chain = []
                    for block in chainJson:
                        newBlock = Block(block['previous_hash'])
                        newBlock.initExisting(block['transactions'], block['nonce'], block['timestamp'])
                        chain.append(newBlock)

                    # check if chain is longer and valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

            except requests.ReadTimeout:
                print(f'could not reach host {node}')
            except requests.ConnectionError:
                print(f'could not reach host {node}')

        # replace our chain if we discovered a longer one
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def mine(self):
        # adding mining reward
        self.nextBlock.new_transaction(
            sender='0',
            recipient=self.node_identifier,
            amount=25,
        )

        proof = self.proof_of_work(self.nextBlock)
        block = self.new_block(proof)
        self.spreadBlock(block)

        return block

    def getBlockchainAsJson(self):
        jsonChain = []
        for block in self.chain:
            jsonChain.append(block.getBlockAsJson())
        return jsonChain

    @staticmethod
    def valid_proof(block, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?

        :param block: <dict> current Block
        :param proof: <int> nonce / proof
        :return: <bool> True if correct, False if not.
        """
        blockHeader = block.blockHeader

        guess = f'{blockHeader["timestamp"]}{blockHeader["merkle"]}{blockHeader["previous_hash"]}{proof}'.encode()
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
        block_string = json.dumps(block.blockHeader, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]
