
"""
Madhuroopa Irukulla

Steps to run the code : If you change the port number in fore_provider.py 
please change the subscriber_address in the main function with the portnumber 
you changed 

run python3 lab3.py cs1.seattleu.edu anyport

 
"""

from datetime import datetime, timedelta
import socket
import sys
import threading
import time
import math

import fxp_bytes
import fxp_bytes_subscriber as fxp_bytes_s
from bellman_ford import BellmanFord  # Import the BellmanFord class from bellmanFord.py

SUB_TIMEOUT = 10 * 60
BUFFER_TIME = 0.1
QUOTE_TIMEOUT = 1.5
DEFAULT_USD_AMOUNT = 100



class Lab3(object):
    def __init__(self, subscriber_address, publisher_address):
        """
        Initialize the Lab3 class.

        Args:
            subscriber_address (tuple): The address of the subscriber.
            publisher_address (tuple): The address of the publisher.
        """
        self.publisher_address = publisher_address
        self.subscriber_address = subscriber_address
        self.graph = {}
        self.bellman_ford = BellmanFord()  # Initialize BellmanFord
        self.timestamps = {}  # Store last update times for currency pairs

    def listen_to_publisher(self):
        """
        Listen to the publisher for incoming data.
        """
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(self.subscriber_address)
        current_time = datetime.now() + (datetime.utcnow() - datetime.now())

        while True:
            byte_msg = listener.recv(1024)
            demarshaled_data = fxp_bytes_s.unmarshal_message(byte_msg)
            print(f"Demarshaled message: {demarshaled_data}")

            for quote in demarshaled_data:
                timestamp = quote["time"]
                time_diff = (current_time - timestamp).total_seconds()
                self.remove_stale_edges()

                if time_diff < BUFFER_TIME:
                    currency_pair = tuple(quote["cross"].split("/"))
                    self.print_log_item("{} {} {} {}".format(timestamp, currency_pair[0], currency_pair[1], quote["price"]))
                    self.add_edge_to_graph(currency_pair, quote)

                else:
                    self.print_log_item("Ignoring out-of-sequence message")

            distances, predecessors, negative_edge = self.bellman_ford.shortest_paths('USD', 1e-15)
            print(f"Negative cycle (Prev Dictionary): {predecessors}")
            print(f"Negative edge: {negative_edge}")

            if negative_edge:
                self.calculate_and_print_arbitrage(predecessors, 'USD', negative_edge)

    def add_edge_to_graph(self, currency_pair, quote):
        """
        Add an edge to the graph and Bellman-Ford algorithm.

        Args:
            currency_pair (tuple): The currency pair.
            quote (dict): The quote data.
        """
        rate = -1 * math.log(quote["price"])
        
        if currency_pair[0] not in self.graph:
            self.graph[currency_pair[0]] = {}

        self.graph[currency_pair[0]][currency_pair[1]] = {"timestamp": quote["time"], "price": rate}
        self.bellman_ford.add_edge(currency_pair[0], currency_pair[1], rate)

        if currency_pair[1] not in self.graph:
            self.graph[currency_pair[1]] = {}

        self.graph[currency_pair[1]][currency_pair[0]] = {"timestamp": quote["time"], "price": -1 * rate}
        self.bellman_ford.add_edge(currency_pair[1], currency_pair[0], -1 * rate)

    def remove_stale_edges(self):
        """
        Remove stale edges from the graph.
        """
        to_remove = []

        for curr1 in self.graph:
            to_remove.clear()

            for curr2 in self.graph[curr1]:
                if (datetime.utcnow() - self.graph[curr1][curr2]["timestamp"]).total_seconds() > QUOTE_TIMEOUT:
                    to_remove.append((curr1, curr2))

            for curr1, curr2 in to_remove:
                self.bellman_ford.remove_edge(curr1, curr2)
                #self.bellman_ford.remove_edge(curr2, curr1)
                del self.graph[curr1][curr2]
                print(f"Removing stale quote for ({curr1}, {curr2})")

    def calculate_and_print_arbitrage(self, predecessors, origin, negative_edge, init_value=DEFAULT_USD_AMOUNT):
        """
        Calculate and print arbitrage opportunities.

        Args:
            predecessors (dict): The predecessors dictionary.
            origin (str): The origin currency.
            negative_edge (tuple): The negative edge tuple.
            init_value (float): The initial USD amount (default is 100).
        """
        current_amount = init_value
        arbitrage_path = []
        steps = [origin]
        final_edge = negative_edge[0]

        while not final_edge == origin:
            steps.append(final_edge)
            final_edge = predecessors[final_edge]

        steps.append(origin)
        steps.reverse()
        previous = origin

        print("ARBITRAGE:")
        print(f"Start with {origin} {init_value}")

        for i in range(1, len(steps)):
            current_currency = steps[i]
            rate = math.exp(-1 * self.bellman_ford.edges[previous][current_currency])
            current_amount *= rate
            test = self.bellman_ford.edges[previous][current_currency]
            arbitrage_path.append(f"Exchange {previous} for {current_currency} at {rate} --> {current_amount}")
            previous = current_currency

        for detail in arbitrage_path:
            print(detail)

        print(f"Final Amount (USD): {current_amount}")
        print(f"Profit: {current_amount - init_value} {origin}")

    def subscribe_to_publisher(self):
        """
        Subscribe to the publisher for updates.
        """
        while True:
            self.print_log_item(f"Sending SUBSCRIBE to {self.publisher_address}")

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                serialized_addr = fxp_bytes_s.serialize_address(self.subscriber_address[0], self.subscriber_address[1])
                sock.sendto(serialized_addr, self.publisher_address)
                sock.close()

            time.sleep(SUB_TIMEOUT)

    def run(self):
        """
        Start the listener and subscriber threads.
        """
        listener_thread = threading.Thread(target=self.listen_to_publisher)
        listener_thread.start()

        subscribe_thread = threading.Thread(target=self.subscribe_to_publisher)
        subscribe_thread.start()

    def print_log_item(self, msg):
        """
        Print log messages with a timestamp.

        Args:
            msg (str): The log message to print.
        """
        print("[" + str(datetime.now()) + "]", msg)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python lab3.py [host] [port]")
        exit(1)

    host, host_port = sys.argv[1], sys.argv[2]
    host_port = int(host_port)

    # Set the subscriber's address
    subscriber_address = (host, host_port)
    publisher_address = ('localhost', 50403)
    subscriber = Lab3(subscriber_address, publisher_address)
    subscriber.run()
