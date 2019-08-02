from subprocess import call
import time

broker = 'python3 -i ../lib/mdbroker.py -port=5555 -v=True'
agent = lambda name, my_summand, service: f"python3 -i ../lib/mdagent.py -broker_ip=localhost -port=5555 -v=True -service={service}" \
    f" --inputs='{{\"my_summand\": {my_summand}}}' {name}"
client = lambda name, target, service: f"python3 -i ../lib/mdclient.py -broker_ip=localhost -port=5555 -v=True -service={service}" \
    f" -d='{{\"num_requests\": 1, \"target\": {target}, \"multiple_bool\": 1}}' {name}"

agents = [
    agent('A01', 2, 'sumnums'),
    agent('A02', 8, 'sumnums')
]

clients = [
    client('C01', 10, 'sumnums')
]


if __name__ == '__main__':
    call(['xfce4-terminal', '-e', broker], shell=False)

    for my_agent in agents:
        call(['xfce4-terminal', '-e', my_agent], shell=False)

    time.sleep(5)       # there has to be some delay while broker/agents stabilize
    for my_client in clients:
        call(['xfce4-terminal', '-e', my_client], shell=False)



