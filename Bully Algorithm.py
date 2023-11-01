import socket
import sys
import random
import pickle
import threading
from enum import Enum

BUFFER_SIZE_CUSTOM = 1024
MAX_CONNECTIONS_CUSTOM = 8
TIMEOUT_LIMIT_CUSTOM = 2.5


## class to represent different states 
class CustomState(Enum):
    INITIAL = 'INITIAL' ##not in an election 
    IN_ELECTION = 'WAIT_FOR_CONFIRMATION' ## waiting for ok while an election message is sent, in an election
    AWAITING_WINNER = 'WAIT_FOR_WINNER'

## class to represent Message protocol
class MessageType(Enum):
    JOIN = 'JOIN'
    ELECTION = 'ELECTION'
    OK = 'OK'
    COORDINATOR = 'COORDINATOR'
    
class Lab2(object):
    def __init__(self, coordinator_host, coordinator_port, days_until_birthday, student_id):
        """
        Initialize a Lab2 instance.

        Parameters:
        - coordinator_host (str): The host of the coordinator.
        - coordinator_port (int): The port of the coordinator.
        - days_until_birthday (int): Number of days until your mother's birthday.
        - student_id (int): The student's ID.
        """
        self.coordinator_host = coordinator_host
        self.coordinator_port = int(coordinator_port)
        self.pid = (int(days_until_birthday), int(student_id))
        self.group = {}
        self.connection_map = {}
        self.current_leader = None
        self.peer_state = CustomState.INITIAL
        self.host_address = "localhost"
        self.port_number = random.randint(1025, 2026)
        self.listener_thread = threading.Thread(target=self.listener_thread_function)

    def run(self):
        """
        Start the Lab2 instance by starting the listener thread, joining the group via GCD, and initiating the election.
        """
        self.listener_thread.start()
        self.join_group()
        self.initiate_election()

    def join_group(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as coordinator_socket:
            coordinator_address = (self.coordinator_host, self.coordinator_port)
            print(f"Connecting to Coordinator at {coordinator_address}")
            coordinator_socket.connect(coordinator_address)
            self.group = self.send_message(coordinator_socket, 'JOIN', (self.host_address, self.port_number))
            print(f"Received the list of {len(self.group)} peers from the Coordinator")
            print(f"List of peers:{self.group}")
            for peer, peer_address in self.group.items():
                self.group[peer] = peer_address

    def initiate_election(self):
        """
        Initiate an election process by checking if the current peer is the leader or not.
        """
        self.peer_state = CustomState.IN_ELECTION
        is_leader = True

        for peer, peer_address in self.group.items():
            if self.is_peer_higher_priority(peer):
                is_leader = False
                self.start_election_thread(peer, peer_address)

        if is_leader:
            self.become_leader()

    def become_leader(self):
        """
        Update the current peer to the leader, change the perr state to Intial(not in election) and notify other peers.
        """
        for peer, peer_address in self.group.items():
            if peer != self.pid:
                self.close_connection(peer)
                self.start_leader_thread(peer, peer_address)

        self.current_leader = self.pid
        self.peer_state = CustomState.INITIAL

    def is_peer_higher_priority(self, peer):
        """
        Check if the given peer has a higher priority than the current peer.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).

        Returns:
        - bool: True if the peer has higher priority, False otherwise.
        """
        return peer[0] > self.pid[0] or (peer[0]== self.pid[0] and peer[1] > self.pid[1])

    def start_election_thread(self, peer, peer_address):
        """
        Start a new thread to send an election message to a peer.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).
        - peer_address (tuple): A tuple representing the peer's address (host, port).
        """
        sender_thread = threading.Thread(
            target=self.send_election_message,
            args=((peer, peer_address), 'ELECTION', self.group)
        )
        sender_thread.start()

    def start_leader_thread(self, peer, peer_address):
        """
        Start a new thread to send a coordinator message to a peer.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).
        - peer_address (tuple): A tuple representing the peer's address (host, port).
        """
        sender_thread = threading.Thread(
            target=self.send_election_message,
            args=((peer, peer_address),'COORDINATOR', self.group)
        )
        sender_thread.start()

    def close_connection(self, peer):
        """
        Close the connection to a peer.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).
        """
        if peer in self.connection_map:
            self.connection_map[peer][0].close()
            del self.connection_map[peer]

    def send_message(self, socket, protocol, message, buffer_size=BUFFER_SIZE_CUSTOM, wait=True):
        """
        Send a message to a socket and optionally wait for a response.

        Parameters:
        - socket: The socket to send the message.
        - protocol (str): The protocol of the message.
        - message: The message to send.
        - buffer_size (int): The size of the message buffer.
        - wait (bool): Whether to wait for a response.

        Returns:
        - Any: The response received, or 500 if an error occurs.
        """
        data = (protocol, (self.pid, message))

        try:
            socket.sendall(pickle.dumps(data))
            if wait:
                return pickle.loads(socket.recv(buffer_size))
        except Exception as e:
            print(e, "message error")
            return 500

    def send_election_message(self, peer, protocol, msg):
        """
        Send an election message to a peer and handle the response.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).
        - protocol (str): The protocol of the message.
        - msg: The message to send.
        """
        socket = self.get_connection(peer)[0]

        print(f"Sending {protocol}")
        send_response = self.send_message(socket, protocol, msg, wait=(protocol != 'COORDINATOR'))

        if send_response and send_response == 500:
            self.connection_map[peer[0]][1] = True

        elif protocol == 'ELECTION' and send_response == 500:
            all_peers_done = all(conn[1] for conn in self.connection_map.values())
            if all_peers_done:
                for conn in self.connection_map:
                    self.connection_map[conn][1] = False
                self.become_leader()

        elif protocol =='ELECTION' and send_response and send_response[0] == 'OK':
            print("Received OK from a peer. Waiting for the coordinator.")
            self.peer_state = CustomState.AWAITING_WINNER

    def listener_thread_function(self):
        """
        Function to run in the listener thread to accept incoming connections and handle messages.
        """
        host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host_socket.bind((self.host_address, self.port_number))
        host_socket.listen(MAX_CONNECTIONS_CUSTOM)

        print(f"Listening on port {self.port_number}")

        while True:
            try:
                peer_socket, peer_address = host_socket.accept()
                print("Accepted connection")
                peer_thread = threading.Thread(target=self.handle_incoming_peer, args=(peer_socket, peer_address))
                peer_thread.start()
            except Exception as e:
                print(e, "error")

    def handle_incoming_peer(self, socket, address):
        """
        Handle incoming messages from a peer.

        Parameters:
        - socket: The socket for communication with the peer.
        - address: The address of the peer.
        """
        msg = pickle.loads(socket.recv(BUFFER_SIZE_CUSTOM))

        protocol = msg[0]
        data = msg[1]

        for peer, peer_address in data[1].items():
            self.group[peer] = peer_address

        if protocol == 'ELECTION':
            print(f"ELECTION message from {address}. Sending OK.")
            self.send_message(socket, 'OK', None, wait=False)

            if self.peer_state != CustomState.IN_ELECTION:
                self.initiate_election()

        elif protocol == 'COORDINATOR':
            self.peer_state = CustomState.INITIAL 
            print("I am the leader now.", data[0])
            self.current_leader = data[0]

        socket.close()

    def get_connection(self, peer):
        """
        Get a connection to a peer or create a new one if needed.

        Parameters:
        - peer (tuple): A tuple representing a peer (days_until_birthday, student_id).

        Returns:
        - list: A list containing the peer's socket and a flag indicating if the connection is open.
        """
        if not peer[0] in self.connection_map or self.connection_map[peer[0]][1]:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(TIMEOUT_LIMIT_CUSTOM)

            try:
                peer_socket.connect(peer[1])
            except Exception as e:
                print(e, "connection error")
                pass
            self.connection_map[peer[0]] = [peer_socket, False]
        return self.connection_map[peer[0]]

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage:\tpython3 custom_lab2.py [coordinator_host] [coordinator_port] [days_until_birthday-integer number days until mother birthday] [student_id]")
        exit(1)

    coordinator_host, coordinator_port, days_until_birthday, student_id = sys.argv[1:5]
    lab2 = Lab2(coordinator_host, coordinator_port, days_until_birthday, student_id)
    lab2.run()
