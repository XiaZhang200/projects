import hashlib
import json
from time import time
from uuid import uuid4
from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        self.nodes=set()
        #genesis block

        self.new_block(previous_hash=1,proof=100)

    def register_nodes(self,address):
        """
        Add a new node to the list of nodes
        address:<str> Address of node.
        return None
        """
        parsed_url =urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chains(self,chain):
        """
        Determine if a given blockchain is valid
        chain:<list> a blockchain
        return bool
        """
        last_block = chain[0]
        current_index = 1

        while current_index<len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n--------------------\n')
            #check that previous hash of the block is  correct

            if block['previous_hash']!=self.hash(last_block):
                return False
            #check PoW is correct´
            if not self.valid_proof(last_block['proof'],block['proof']):
                return False
            
            last_block = block
            current_index+=1
            return True
    
    def resolve_conflicts(self):
        """
        Consensus Algorithm, replaces our chain with the longest one in the network.
        return <bool> True if replaced , false if not
        """
        neighbours = self.nodes
        new_chain=None
        max_length=len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code ==200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chains(chain):
                    max_length = length
                    new_chain = chain
            
            if new_chain:
                self.chain=new_chain
                return True
            return False


    def new_block(self,proof,previous_hash=None):
        """
            Create a new block in the Blockchain
            proof : <int> Proof given by Proof of Work Alg.
            previous_hash : (Optional) <str> Hash of previous Block
            return : <dict> new Block
        """
        block = {
            'index':len(self.chain)+1,
            'timestamp': time(),
            'transactions':self.current_transaction,
            'proof':proof,
            'previous_hash':previous_hash or self.hash(self.chain[-1]),
        }

            #reset current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block
        
    def new_transaction(self,sender,recipient,amount):
        """
            Creates a new transaction to go into the next mined Block
            sender : <str> Address of Sender
            recipient : <str> Address of Recipient
            amount : <int> Amount
        """
        self.current_transaction.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount,
         })

        return self.last_block['index']+1

    @staticmethod
    def hash(block):
        """
            Creates a SHA-256 hash of a Block
            block : <dict> Block
            return <str>
        """
        #must ensure dictionaries are ordered
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self,last_proof):
        """
            Simple Proof of Work Alg:
            - Find a number p s.t. hash(pp') contains leading 4 zeros, where p
            - p is the previous proof and p' is the new proof
            last_proof : <int>
            return <int>
        """

        proof = 0
        while self.valid_proof(last_proof,proof) is False:
            proof +=1
            
        return proof

    @staticmethod
    def valid_proof(last_proof,proof):
        """
            Validates the proof: Does hash(pp') contain 4 leading zeros?
            last_proof : <int> Previous proof
            proof : <int> Current proof
            return <bool> True if correct,False if not
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4]== "0000"

#instantiate node
app = Flask(__name__)

#generate global unique address for this node
node_identifier = str(uuid4()).replace('-','')

#Instantiate blockchain

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new',methods=['POST'])
def new_transaction():
    values = request.get_json()
    #check required data is present in POST data
    required = ['sender','recipient','amount']
    if not all(k in values for k in required):
        return 'Missing values',400

    #create a new transaction
    index = blockchain.new_transaction(values['sender'],values['recipient'],values['amount'])
    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response),201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register',methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error. Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_nodes(node)

    response={
        'message': "New nodes have been added",
        'total_nodes' : list(blockchain.nodes)
    }
    return jsonify(response),201

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

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)