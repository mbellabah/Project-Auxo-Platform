# Brief Overview of the System
pass 

# Initializing the Broker, Agent and Client
To initialize the broker, in the terminal run: `python3 mdbroker.py -port=5555 -v=True`

To initialize an agent with the sumnums service worker on start, in the terminal run: 
`python3 mdagent.py -broker_ip=localhost -port=5555 -v=True -service=sumnums --inputs='{"my_summand": 2}' A01`

To initialize a client asking for the sumnnums service, in the terminal run: 
`python3 mdclient.py -broker_ip=localhost -port=5555 -v=True -service=sumnums -d='{"num_requests": 1, "target": 10, "multiple_bool": 1}' C01`

# Description of the Services
* **ECHO**
    * Input (client side):
    * Function: 
* **SUMNUMS**