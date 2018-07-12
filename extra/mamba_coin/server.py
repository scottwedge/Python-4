#!/usr/bin/python

"""

    NODE/MINER SERVER
    THIS SCRIPT SHOULD BE DEPLOYED TO ALL 
    NODES ACROSS THE NETWORK

        INSTALLATION/USAGE INSTRUCTIONS:
            1. HAVE SERVER SCRIPT RUNNING
            2. ADD A KNOWN HOST:PORT BY CALLING /add_peer GET api
            3. SYNC NODES BY CALLING /sync_nodes GET api
            4. SYNC BLOCKS BY CALLING /sync_blocks GET api
            5. SYNC TRANSACTIONS BY CALLING /sync_trans GET api
            6. POST ANY TRANSACTIONS BY CALLING /submit_transactions POST api
*           7. MINE BY CALLING /mine GET api


"""
##################################################################################################################################################

# SERVER : 
# one node = one miner = one computer = one host machine on the mambacoin network


# sample transactions from each data of a block: (JSON object)
#{
#    "timestamp": str(datetime.datetime.now())
#    "from": "asdf-random-public-key-asdfasdf"
#    "to": "asdfas-random-public-key-asdfasdf"
#    "amount": 1
#
#}

##################################################################################################################################################

# importing required modules
from flask import Flask                                                 # for our http server
from flask import request                                               # for http server's request module
from resources import Block                                             # for blockchain class operations
from resources import Helper                                            # for helper class operations
import sys                                                              # for system program implementation
import json                                                             # for json loading and dumping
import datetime                                                         # for time operations
import requests                                                         # for http request operations

##################################################################################################################################################

class Server:
    """
        superClass: None

        class respnsible for running a server 
        at each node of the network
        interacts with Helper and Block class internally
        but also interacts with user externally
        

    """

#==================================================== CLASS VARIABLES ===========================================================================

    node = Flask(__name__)                          # telling flask this file name will be the name of where our web server lives
    
    this_node_transactions = []                     # initalize list of transactions for this node
    blockchain             = []                     # initialize list of blockchains for this node
    peer_nodes             = []                     # initialize list of peer nodes on this node
    
    helper       = Helper()                         # initialize our helpers
    node_helper  = helper.Node_helper()
    block_helper = helper.Blockchain_helper()
    trans_helper = helper.Transaction_helper()

    miner_address = "asdfasd-random-miner-address-1233123412asdfl3k4j"          # setting a random public address

#=================================================== INSTANCE METHODS ============================================================================


    def _usage(self):
        print "\n\n"
        
        print """
        
        [+] Welcome to Mambacoin network server node
        
        [+] Current time is: %s 
        [+] External program dependencies: cURL 

            $ curl "host:port/add_peer/?host=<host>&port=<port>"        ---- Add peer node to node list
            $ curl "host:port/sync_nodes"                               ---- Sync node list
            $ curl "host:port/sync_blocks"                              ---- Sync blockchain list
            $ curl "host:port/sync_trans"                               ---- Sync transaction list 
            $ curl "host:port/submit_transactions" \\                   ---- Post transactions to node
                    -H "application/json"          \\
                    -d "{"timestamp":<transaction timestamp>,\\
                         "from"     : <transaction from address>, \\
                         "to"       : <transaction to address>, \\
                         "amount"   : <transaction ammount>}"
            $ curl "host:port/mine"                                     ---- Mine mamba coin and solidify all transactions since last mine

        
        [+] This project is derived from snakecoin: https://medium.com/crypto-currently/lets-build-the-tiniest-blockchain-e70965a248b
        
        """ %str(datetime.datetime.now())

        print "\n\n"

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# transaction related handlers and methods

    def _check_trans(self, transaction):
        """
            param1 obj: self object
            param2 dict: a transaction dictionary to be checked

            return bool: whether or not this node's transaction list contains the transactions

            This is an internal private api called by
            this node's submit_transaction_handler method
        
        """

        for t in Server.this_node_transactions:                     # iterating through current list of transactions 
            if json.dumps(transaction) == json.dumps(t):            # if input new trans is the same as any of our list, return false
                return False

        return True                                                 # if not, return true

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def submit_transaction_handler(self):
        """
            param1 obj: self object
            return sideeffect: handler listens to POST request of /submit_transaction api
            
            This is an external api called by
            any user to post transcations
            
            Also this is an internal api called by
            peer nodes whenever a transaction is posted there
        
        """

        if request.method == 'POST':                                                    # make sure only handle post requests
            new_trans = json.loads(request.get_json())                                  # extracting the transaction data    
            
            if self._check_trans(new_trans) == True:                                    # making sure transactions are actually new

                # added feature as per bitcoin white paper
                try:
                    for peer in Server.peer_nodes:
                        requests.post("http://{}/submit_transaction", json=new_trans)   # broadcast to other nodes
                except:
                    pass

                Server.this_node_transactions.append(new_trans)                         # adding new transactions to this node's list
    
                # standard output our transaction
                print "=================================================="
                print "**New Transaction**"
                print "From: {}".format(new_trans['from'])
                print "To: {}".format(new_trans['to'])
                print "Amount: {}".format(new_trans['amount'])                          
    
                return "Transaction submission successful\n"                            # response through server

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def clear_trans_handler(self):
        """
            param1 obj: self object
            return sideeffect: handler listens to DELETE request of /clear_trans api

            This is an internal api called by
            peer  node's mining functionality to clear 
            this node's transactions after a block is mined with all transactions
        
        """

        if request.method == 'DELETE':
            Server.this_node_transactions[:] = Server.trans_helper.ensure()     # clears transaction, this is called by miners of other nodes 
                                                                                # either we get an empty trans list or remaining unsynced trans
                                                                                # if there are any
        return ""                                                               # NOTE: ensure method will ensure all transactions are either
                                                                                # accounted and cleared/deleted, or have the remaining 
                                                                                # unaccounted transactions

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def sync_trans_handler(self):                                               
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /sync_trans api

            This is an external api called by 
            any user to sync this node's transactions with others
        
        """

        # trans_helper.consensus will update transaction list according to its policies (rn its the longest, could be improved)
        Server.this_node_transactions[:] = Server.trans_helper.consensus(Server.this_node_transactions, Server.peer_nodes)

        return "\n[+] Transactions synced: {}".format(str(Server.this_node_transactions))

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def get_trans_handler(self):                            
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /sync_trans api

            This is an internal api called by
            peer nodes to extract this node's 
            transactions for syncing purposes
        
        """
        # return json format of this node's transaction list
        return json.dumps(Server.this_node_transactions)                    

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # block related handlers and methods

    def sync_blocks_handler(self):  
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /sync_blocks api
            
            This is an external api called by 
            any user to sync this node's block
        
        """
        
        # block_helper.consensus will update the blockchain list according to its policies (rn its longest as well)
        Server.blockchain[:] = Server.block_helper.consensus(Server.blockchain, Server.peer_nodes)
        
        return "\n[+] Blocks synced: {}".format(str(Server.blockchain))

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def get_blocks_handler(self):  
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /get_blocks api

            This is an internal api called by 
            peer nodes to extract this node's 
            blockchain list for syncing purposes
        
        """

        blocks = []
        
        for block in Server.blockchain:                                         # remember block is in block object format
            blocks.append({
                    "index"    : block.index,                                   # block.index is int 
                    "timestamp": str(block.timestamp),
                    "data"     : block.data,                                    # block.data is in dict format
                    "hash"     : str(block.hash)
                })


        return json.dumps(blocks)                                               # return json format through the server

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # peer nodes related handlers and methods

    def sync_nodes_handler(self):   
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /sync_nodes api

            This is an external api called by 
            any user to sync this node's 
            peer node list
        
        """

        # node_helper.consensus updates the peer nodes list according to its policies 
        # (every possible node's address is checked and added if need)
        # since nodes are added alot less than blocks and transactions, we can afford to do this for now.
        Server.peer_nodes[:] = Server.node_helper.consensus(Server.peer_nodes)

        return "\n[+] Nodes synced: {}".format(str(Server.peer_nodes))

#-------------------------------------------------------------------------------------------------------------------------------------------------

    def get_nodes_handler(self):
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /get_nodes api

            This is an interal api called by
            peer nodes to extract this node's 
            peer nodes list for syncing purposes
        
        """
        nodes = []

        for n in Server.peer_nodes:                                 # converting into json objects to be sent via http requests
            host = n.split(':')[0]
            port = n.split(':')[1]
            node = {
                "host": str(host),
                "port": str(port)
            }
            
            nodes.append(node)

        return json.dumps(nodes)                                    # after syncing everyting, convert synced nodes to json and send thru server 

#------------------------------------------------------------------------------------------------------------------------------------------------

    def add_peer_handler(self):
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /add_peer api

            This is an external api called by
            any user to add a host node onto this 
            particular node's peer node list
        
        """
        
        # args is a dict of key value pairs of the url query, after ?
        # url format: http://192.168.1.249:5000/add_peer/?host=192.168.1.10&port=50

        if request.method == "GET":
            host = request.args['host'] if 'host' in request.args else 'localhost'
                                                                               
            port = request.args['port']                                         
            peer = host + ':' + port
            Server.peer_nodes.append(peer)
        
        
        return '\n[+] peer added: {}'.format(peer)                              # response thru server

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # mining handler and method

    def mine_handler(self):
        """
            param1 obj: self object
            return sideeffect: handler listens to GET request of /mine api

            This is an external api called by 
            any user to mine a mamba coin 
            (Kobe's face in front, coin value in back)
            and lock in all transactions since the last mined coin, 
            add the mine coin with new proof of work with the locked in
            transactions, unto to the network blockchain list
        
        """

        # before mining, sync nodes, blocks, and transactions
        Server.peer_nodes[:] = Server.node_helper.consensus(Server.peer_nodes)             
        Server.blockchain[:] = Server.block_helper.consensus(Server.blockchain, Server.peer_nodes)   
        Server.this_node_transactions[:] = Server.trans_helper.consensus(Server.this_node_transactions, Server.peer_nodes) 

        # after the first sync, lets see if a genesis block is present
        if len(Server.blockchain) == 0:
            Server.blockchain.append(Block.create_genesis_block())              # if not, create genesis block to start chain for network
    
        # start mining
        last_block = Server.blockchain[len(Server.blockchain) - 1]              # grabbing the last block 
        last_proof = last_block.data['proof-of-work']                           # grabbing the proof of work from the last block
        proof = Server.helper.proof_of_work(last_proof)                         # generating a new proof from the last one                            
        miner_transaction = {                                                   # adding miner transactions
                "timestamp": str(datetime.datetime.now()),
                "from"     : "network",
                "to"       : Server.miner_address,
                "amount"   : 1
            }

        Server.this_node_transactions.append(miner_transaction)                 # append the new transaction to the transaction list

        data = {                                                                # the data property of a mamba coin
                "proof-of-work" : proof,
                "transactions" : list(Server.this_node_transactions)
            }

        block = Block(last_block.index + 1, datetime.datetime.now(), data, prev_hash=last_block.hash) 
        Server.blockchain.append(block)                                                 # adding block to chain

        # clean up
        for peer in Server.peer_nodes:                                                  # empty the accounted transactions 
            try: 
                requests.delete("http://{}/clear_trans".format(peer))                   # clear_trans api will check for any unaccounted 
            except:                                                                     # transactions in other node's so they are not deleted
                pass
                                                                                        
        Server.this_node_transactions[:] = []                                           # clear this node's transactions 
        
                                                                                        # resyncing to account for any slight discrepancies 
                                                                                        # that may happen between last sync and mining procedure
        Server.peer_nodes[:] = Server.node_helper.consensus(Server.peer_nodes)          # resync peer_nodes, and blocks, and trans
        Server.blockchain[:] = Server.block_helper.consensus(Server.blockchain, Server.peer_nodes)# becareful with this sync
        Server.this_node_transactions[:] = Server.trans_helper.consensus(Server.this_node_transactions, Server.peer_nodes) 


        return json.dumps({                                                             # response thru server
                "index": block.index,
                "timestamp": str(block.timestamp),
                "data": block.data, 
                "hash": str(block.hash)
            }) + "\n"
    
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    

    def start(self, port=None):
        """
        param1 obj: self object
        param2 str: port number default to 5000
        return sideeffect: server initializes/setup routing code
        
        using flask's routing decorator to route, 
        the decorated function will return the response for the appropriate url routing
        and handle this url routing appropriatly

        """
        # once called, it will use the same data and post to all nodes
        @Server.node.route('/submit_transaction', methods=['POST'])
        def submit_transaction(): return self.submit_transaction_handler() 

        # once called, it will call /get_trans to retrieve all transactions from peers and consensus the best one to be updated
        @Server.node.route('/sync_trans', methods=['GET'])
        def sync_trans(): return self.sync_trans_handler()

        # called by /sync_trans api 
        @Server.node.route('/get_trans', methods=['GET'])
        def get_trans(): return self.get_trans_handler()
    
        # once called, it will call /get_blocks to retreive all blocks from all peers and consensus the best one to be updated
        @Server.node.route('/sync_blocks', methods=['GET'])
        def sync_blocks(): return self.sync_blocks_handler()

        # called by /sync_blocks rest api
        @Server.node.route('/get_blocks', methods=['GET'])
        def get_blocks(): return self.blocks_handler()
    
        # once called it will call /get_nodes to retrieve all nodes from peers and consensus the best one to be updated
        @Server.node.route('/sync_nodes', methods=['GET'])
        def sync_nodes(): return self.sync_nodes_handler()

        # called by /sync_nodes
        @Server.node.route('/get_nodes', methods=['GET'])
        def get_nodes(): return self.nodes_handler()

        # once called it will add a host and port to this server's nodes list
        @Server.node.route('/add_peer', methods=['GET'])
        def add_peer(): return self.add_peer_handler()
    
        # once called it will mine a coin using proof of work, and clear transactions of this server, 
        # call /clear_trans to all other nodes to clear/delete accounted transactions
        @Server.node.route('/mine', methods=['GET'])
        def mine(): return self.mine_handler()
        
        # called by /mine api to clear all transactions across network
        @Server.node.route('/clear_trans', methods=['DELETE'])
        def clear_trans(): return self.clear_trans_handler()

        # making sure webserver will be running eternally, standard port is 5000
        try:
            Server.node.run(port=port)
        except:
            print "\n[!] Server had trouble starting at port {}".format(port)
            print "[!] Exiting..."
            sys.exit(1)
    
##################################################################################################################################################

# script execution

if __name__ == "__main__":
    try:
        server = Server()                        # initializing server
        server._usage()                          # displaying usage details
        if len(sys.argv) > 1:
            port = sys.argv[1] 
            server.start(port=port)              # starting server
        else:
            server.start()
    except KeyboardInterrupt:
        print "[!] Requested shutdown, exiting..."
        sys.exit(0)
