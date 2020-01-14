import json
import time
import copy
from typing import List, Dict

from torchvision import datasets, transforms
import torch

from auxo_olympus.lib.entities.mdwrkapi import MajorDomoWorker
from auxo_olympus.lib.services.service_exe import ServiceExeBase

from auxo_olympus.lib.services.serviceExeFederatedLearning.models.nets import CNNMnist
from auxo_olympus.lib.services.serviceExeFederatedLearning.fed.Fed import fed_avg
from auxo_olympus.lib.services.serviceExeFederatedLearning.models.update import LocalUpdate
from auxo_olympus.lib.services.serviceExeFederatedLearning.fed.sampling import mnist_iid, raw_args


class ServiceExeFederatedLearning(ServiceExeBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.service_name = 'federatedlearning'
        self.name = f'{self.service_name}-Thread'
        self.num_devices = 0 

    def process(self, *args) -> dict:
        try:
            request: dict = json.loads(args[0])
            worker: MajorDomoWorker = args[1]
        except IndexError:
            raise IndexError('Error: worker object has not been supplied:')

        self.worker = worker
        self.peer_port = worker.peer_port

        assert self.peer_port, "This service requires peers to exist!"
        assert self.inputs, "Need to provide kwargs when initing service"

        # let agent who holds the service-exe know that it has received a request by signaling on the got_req_q
        self.got_req_q.put('ADD')

        # Extract relevant details from the requests and inputs
        num_agents: int = len(self.peer_port.peers) + 1
        dataset: str = str(request['dataset'])
        epochs: int = raw_args.epochs
        gpu: int = 0
        device = torch.device('cuda:{}'.format(gpu) if torch.cuda.is_available() and gpu != -1 else 'cpu')
        raw_args.device = device

        if dataset == 'mnist':
            # For now,
            trans_mnist = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
            dataset_train = datasets.MNIST(f'../services/serviceExeFederatedLearning/data_{self.agent_name}/mnist/', train=True, download=True, transform=trans_mnist)
            # dataset_test = datasets.MNIST('../services/serviceExeFederatedLearning/data/mnist/', train=False, download=True, transform=trans_mnist)
            
            # get training data indices (here we assume that the agent does not have access to other)
            my_data_indxs = mnist_iid(dataset_train, num_agents)[self.agent_id - 1]
        else:
            exit('Error: unrecognized dataset')
        img_size = dataset_train[0][0].shape

        # Connect peer_port to all the peers -- Note that the worker possesses the peer port
        self.peer_port.tie_to_peers()
        time.sleep(self.BIND_WAIT)

        # Populate the peer-ports state-space
        self.peer_port.state_space['local'] = LocalUpdate(args=raw_args, dataset=dataset_train, idxs=my_data_indxs)

        if self.leader_bool:
            net_glob = CNNMnist().to(device)

            print(self.agent_name, net_glob)
            print("#"*20)

            net_glob.train()

            # copy weights
            w_glob = net_glob.state_dict()

            # training
            loss_train = []

            for iter in range(epochs):
                w_locals, loss_locals = [], []

                # request from peers
                send_to: List[bytes] or Dict[bytes, str] = self.peer_port.peers

                # train self
                w, loss = self.peer_port.state_space['local'].train(net=copy.deepcopy(net_glob).to(device))
                w_locals.append(copy.deepcopy(w))
                loss_locals.append(copy.deepcopy(loss))

                # get all the others to train themselves and provide the necessary info
                self.request_from_peers(state='local', send_to=send_to)
                for data in self.peer_port.state_space['other_peer_data'].values():
                    # print(self.peer_port.state_space['other_peer_data'])
                    w, loss = data['local'].train(net=copy.deepcopy(net_glob).to(device))
                    w_locals.append(copy.deepcopy(w))
                    loss_locals.append(copy.deepcopy(loss))

                # update the global weights
                w_glob = fed_avg(w_locals)

                # copy weight to net_glob
                net_glob.load_state_dict(w_glob)

                # print loss
                print(f"{self.agent_name}-{self.service_name} REPORTING")
                loss_avg = sum(loss_locals) / len(loss_locals)
                print('Round {:3d}, Average loss {:.3f}'.format(iter, loss_avg))
                loss_train.append(loss_avg)

            # Formulate the reply
            payload = "NET DONE"
            reply = {'reply': payload, 'origin': self.worker_name}

            # inform peers that leader is done and so they can die
            self.inform_peers(send_to=send_to)  # Peers that are not leaders will shutdown themselves
            self.peer_port.stop()

            return reply
        else:
            while self.peer_port.leader_force_alive:
                pass


if __name__ == '__main__':
    pass
    # args = args_parser()
    # args.device = torch.device('cuda:{}'.format(args.gpu) if torch.cuda.is_available() and args.gpu != -1 else 'cpu')
    #
    # # load dataset and split users
    # if args.dataset == 'mnist':
    #     trans_mnist = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    #     dataset_train = datasets.MNIST('../data/mnist/', train=True, download=True, transform=trans_mnist)
    #     dataset_test = datasets.MNIST('../data/mnist/', train=False, download=True, transform=trans_mnist)
    #
    #     dict_devices = mnist_iid(dataset_train, args.num_devices)
    #
    # else:
    #     exit('Error: unrecognized dataset')
    #
    # img_size = dataset_train[0][0].shape
    #
    # # build the model
    # if args.model == 'cnn' and args.dataset == 'mnist':
    #     net_glob = CNNMnist(args=args).to(args.device)
    # else:
    #     exit('Error: unrecognized model')
    #
    # print(net_glob)
    # net_glob.train()
    #
    # # copy weights
    # w_glob = net_glob.state_dict()
    #
    # # training
    # loss_train = []
    # cv_loss, cv_acc = [], []
    # val_loss_pre, counter = 0, 0
    # net_best = None
    # best_loss = None
    # val_acc_list, net_list = [], []
    #
    # for iter in range(args.epochs):
    #     w_locals, loss_locals = [], []
    #     m = max(int(args.frac * args.num_devices), 1)
    #     idxs_devices = np.random.choice(range(args.num_devices), m, replace=False)
    #     for idx in idxs_devices:
    #         local = LocalUpdate(args=args, dataset=dataset_train, idxs=dict_devices[idx])
    #         w, loss = local.train(net=copy.deepcopy(net_glob).to(args.device))
    #         w_locals.append(copy.deepcopy(w))
    #         loss_locals.append(copy.deepcopy(loss))
    #
    #     # update global weights
    #     w_glob = fed_avg(w_locals)
    #
    #     # copy weight to net_glob
    #     net_glob.load_state_dict(w_glob)
    #
    #     # print loss
    #     loss_avg = sum(loss_locals) / len(loss_locals)
    #     print('Round {:3d}, Average loss {:.3f}'.format(iter, loss_avg))
    #     loss_train.append(loss_avg)
    #
    # # plot loss curve
    # plt.figure()
    # plt.plot(range(len(loss_train)), loss_train)
    # plt.ylabel('train_loss')
    # plt.savefig(
    #     './log/fed_{}_{}_{}_C{}_iid{}.png'.format(args.dataset, args.model, args.epochs, args.frac, args.iid))
    #
    # # testing
    # net_glob.eval()
    # acc_train, loss_train = test_img(net_glob, dataset_train, args)
    # acc_test, loss_test = test_img(net_glob, dataset_test, args)
    # print("Training accuracy: {:.2f}".format(acc_train))
    # print("Testing accuracy: {:.2f}".format(acc_test))


