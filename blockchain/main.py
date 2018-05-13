import json
from uuid import uuid4
import flask
from blockchain import Blockchain

# instantiate node (start flask)
app = flask.Flask(__name__)

# generate unique node address
node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # get the next proof of work
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # adding mining reward
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )

    # add new block to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return flask.jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = flask.request.get_json()

    # check for required data
    required = ['sender', 'recipient', 'amount']
    if values is None or not all(k in values for k in required):
        return 'Missing values', 400

    # add new transaction to blockchain object
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {
        'message': f'Transaction will be added to Block {index}'
    }

    return flask.jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return flask.jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

