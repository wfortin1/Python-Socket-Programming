# Import statements
import socket
import signal
import sys
import argparse
from urllib.parse import urlparse

# Discovery port constant

DISCOVERY_PORT = 8000

# Discovery socket

discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Dictionary storing (room => url) key value pairs.

room_dict = {}

# Signal handler to handle ctrl-c .

def signal_handler(sig, frame):
  print('Interrupt received, shutting down...')

  # Terminate every server registered with the discovery service.

  for room_name in room_dict:
    room_url = urlparse(room_dict[room_name])
    server_addr = (room_url.hostname, room_url.port)
    discovery_socket.sendto('SERVER TERMINATE'.encode(), server_addr)

  # Exit the program.
  sys.exit(0)


# Function to process messages from client's/server's.

def process_message(message, addr):
  # Split the message

  print(message)
  words = message.split()

  # REGISTER command

  if (words[0] == 'REGISTER'):

    # Should be of the form REGISTER <url> <name>

    if (len(words) == 3):

      # If it is in the dictionary, return NOTOK already registered.

      if words[2] in room_dict.keys():
        return f'NOTOK The room {words[2]} has already been registered.'

      # Otherwise add it to dict and return OK

      room_dict[words[2]] = words[1]
      return f'OK The room {words[2]} has been registered.'
    else:
      return 'NOTOK Invalid command.'

  # DEREGISTER command

  elif (words[0] == 'DEREGISTER'):

    # Should be of the form DEREGISTER <room>

    if(len(words) == 2):

      # If it is in the dict, remove it and send OK message.

      if (words[1] in room_dict.keys()):
        room_dict.pop(words[1])
        return f'OK The room {words[1]} has been deregistered.'
      # Otherwise return NOTOK

      else:
        return f'NOTOK The room {words[1]} is not registered'
    else:
      return 'NOTOK Invalid command'

  # LOOKUP command

  elif (words[0] == 'LOOKUP'):

    # Should be of the form LOOKUP <name>
    if (len(words) == 2):

      # If it is in the dict, return OK and URL

      if (words[1] in room_dict.keys()):
        return f'OK {room_dict[words[1]]}'

      # Otherwise return NOTOK, room not registered.

      else:
        return f'NOTOK The room {words[1]} is not registered.'
    else:
      return 'NOTOK Invalid command'
  else:
    return 'NOTOK Invalid command'

# Main method

def main():
  global discovery_socket

  # Register our signal handler for shutting down.

  signal.signal(signal.SIGINT, signal_handler)

  print('Discovery Service Started\n')

  # Bind discovery socket to correct server.

  discovery_socket.bind(('', DISCOVERY_PORT))
  print('\nDiscovery service will wait for input at port ' + str(discovery_socket.getsockname()[1]))

  # Loop forever waiting for messages from other servers.

  while True:
    # Get message and address from socket

    message, addr = discovery_socket.recvfrom(1024)

    # Process the input and generate a response

    response = process_message(message.decode(), addr)

    # Send the response out to the address.

    discovery_socket.sendto(response.encode(), addr)


if __name__ == '__main__':
  main()


