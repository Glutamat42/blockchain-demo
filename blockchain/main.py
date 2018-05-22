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
    block = blockchain.mine()

    response = {
        'message': 'New Block Forged',
        'timestamp': block.blockTime,
        'merkle': block.transactionsHash,
        'transactions': block.transactions,
        'proof': block.nonce,
        'previous_hash': block.prevHash
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
    index = blockchain.newTransaction(values['sender'], values['recipient'], values['amount'])

    response = {
        'message': f'Transaction with added with id {index}'
    }

    return flask.jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.getBlockchainAsJson(),
        'length': len(blockchain.getBlockchainAsJson())
    }
    return flask.jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = flask.request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return 'Error: Please submit a valid list of nodes', 400

    for node in nodes:
        blockchain.nodes.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes.nodes),
    }
    return flask.jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return flask.jsonify(response), 200


@app.route('/transactions/add', methods=['POST'])
def addTransactions():
    values = flask.request.get_json()

    blockchain.receivedTransactions(values['transactions'])

    return flask.jsonify(), 200


@app.route('/block/add', methods=['POST'])
def addBlock():
    values = flask.request.get_json()

    blockchain.receivedBlock(values['block'])

    return flask.jsonify(), 200


if __name__ == '__main__':
    port = 5000
    print(f'port: {port}')
    app.run(host='0.0.0.0', port=port)















