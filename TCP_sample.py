<<<<<<< HEAD
import socket
import pickle
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <hostname> <port>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])

    try:
        # Create a socket to connect to the GCD
        #socket.socket() constructor, specifying the socket family (e.g., socket.AF_INET for IPv4) 
        # and socket type (e.g., socket.SOCK_STREAM for TCP or socket.SOCK_DGRAM for UDP).
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd_socket:
            gcd_socket.connect((hostname, port))

            # Send JOIN message to GCD
            join_message = pickle.dumps('JOIN')
            gcd_socket.send(join_message)

            # Receive potential group members
            group_members_data = gcd_socket.recv(1024)
            group_members = pickle.loads(group_members_data)

            for member in group_members:
                member_host = member['host']
                member_port = member['port']

                # Create a socket to connect to group members
                #socket.AF_INET used ipv4 addressing 
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as member_socket:
                    member_socket.settimeout(1.5)  # Set a 1500ms timeout

                    try:
                        member_socket.connect((member_host, member_port))

                        # Send HELLO message to group member
                        hello_message = pickle.dumps('HELLO')
                        member_socket.send(hello_message)

                        # Receive and print the response
                        response_data = member_socket.recv(1024)
                        response = pickle.loads(response_data)
                        print(f"Response from {member_host}:{member_port}: {response}")

                    except socket.timeout:
                        print(f"Timeout error connecting to {member_host}:{member_port}")

                    except Exception as e:
                        print(f"Error connecting to {member_host}:{member_port}: {e}")

    except ConnectionRefusedError:
        print("Failed to connect to the GCD. Check the hostname and port.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
=======
import socket
import pickle
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <hostname> <port>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])

    try:
        # Create a socket to connect to the GCD
        #socket.socket() constructor, specifying the socket family (e.g., socket.AF_INET for IPv4) 
        # and socket type (e.g., socket.SOCK_STREAM for TCP or socket.SOCK_DGRAM for UDP).
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd_socket:
            gcd_socket.connect((hostname, port))

            # Send JOIN message to GCD
            join_message = pickle.dumps('JOIN')
            gcd_socket.send(join_message)

            # Receive potential group members
            group_members_data = gcd_socket.recv(1024)
            group_members = pickle.loads(group_members_data)

            for member in group_members:
                member_host = member['host']
                member_port = member['port']

                # Create a socket to connect to group members
                #socket.AF_INET used ipv4 addressing 
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as member_socket:
                    member_socket.settimeout(1.5)  # Set a 1500ms timeout

                    try:
                        member_socket.connect((member_host, member_port))

                        # Send HELLO message to group member
                        hello_message = pickle.dumps('HELLO')
                        member_socket.send(hello_message)

                        # Receive and print the response
                        response_data = member_socket.recv(1024)
                        response = pickle.loads(response_data)
                        print(f"Response from {member_host}:{member_port}: {response}")

                    except socket.timeout:
                        print(f"Timeout error connecting to {member_host}:{member_port}")

                    except Exception as e:
                        print(f"Error connecting to {member_host}:{member_port}: {e}")

    except ConnectionRefusedError:
        print("Failed to connect to the GCD. Check the hostname and port.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
>>>>>>> 553721996809aa4b10c0b721d24e75a6ef486173
