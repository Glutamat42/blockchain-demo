import hashlib
import json
import time
from uuid import uuid4


class Block:
    def __init__(self, prevHash):
        self.transactions = []
        self.prevHash = prevHash
        self.blockTime = time.time()
        self.nonce = None

    def initExisting(self, transactions, nonce, timestamp):
        self.transactions = transactions
        self.nonce = nonce
        self.blockTime = timestamp

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

        self.transactions.append(newTx)

        return newTx['txid']

    def getTxById(self, txid):
        for tx in self.transactions:
            if tx['txid'] is txid:
                return tx
        return None

    def getBlockAsJson(self):
        json = {
            'timestamp': self.blockTime,
            'merkle': self.transactionsHash,
            'transactions': self.transactions,
            'previous_hash': self.prevHash,
            'nonce': self.nonce,
        }
        return json

    @property
    def transactionsHash(self):
        block_string = json.dumps(self.transactions, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def blockHeader(self):
        # refresh block time if nonce is not found
        if self.nonce is None:
            self.blockTime = time.time()

        header = {
            'timestamp': self.blockTime,
            'merkle': self.transactionsHash,
            'previous_hash': self.prevHash,
            'nonce': self.nonce
        }
        return header
