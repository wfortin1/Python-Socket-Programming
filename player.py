# import statements
import socket
import signal
import sys
import argparse
from urllib.parse import urlparse
import selectors

###############################################
# Sample commands for 3 players and 4 rooms   #
###############################################
# python3 discovery.py
# python3 room.py "study" "There are lot's of books... There is a kitchen to the east and a living room to the south." "book" "scotch" "globe" -e "kitchen" -s "living"
# python3 room.py "kitchen" "A kitchen, there is a study to the west, and an opening to a backyard to the south" "bannana" "apple" "knife" -w "study" -s "backyard"
# python3 room.py "living" "Living room there is 2 couches and a large glass window. There is a study to the north, and a backyard to the east" "letter" "pen" "pillow" -n "study" -e "backyard"
# python3 room.py "backyard" "Lot's of open green space, looks like it's fenced off. There is a living room to the west and a kitchen to the north" "ball" "gnome" "bones" -n "kitchen" -w "living"
# python3 player.py wfortin study
# python3 player.py potatoman study
# python3 player.py hydraliske study
##############################################

# Discovery server constant

DISCOVERY_SERVER = ('localhost', 8000)

# Socket timeout in seconds constant

SOCKET_TIMEOUT = 5

# Socket for sending messages.

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address.

server = ('', '')

# User name for player.

name = ''

# Inventory of items.

inventory = []

# Direction List

direction_list = ['north', 'south', 'west', 'east', 'up', 'down']

# Signal handler for graceful exiting.  Let the server know when we're gone.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')

    # Exit the server

    message='exit'
    client_socket.sendto(message.encode(), server)

    # Remove all items from player's inventory

    for item in inventory:
        message = f'drop {item}'
        client_socket.sendto(message.encode(), server)
    sys.exit(0)

# Simple function for setting up a prompt for the user.

def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)


# Function to join a room.

def join_room(room_name):
    global server

    # Checck to see if the room is in the discovery service and split up the response

    message = f'LOOKUP {room_name}'
    client_socket.sendto(message.encode(), DISCOVERY_SERVER)
    response, addr = client_socket.recvfrom(1024)
    command = response.decode().split()

    # If the response is OK then continue joining the room.

    if (command[0] != 'NOTOK'):

        # Setup server variable.
        server_address = urlparse(command[1])
        server = (server_address.hostname, server_address.port)

        # Send join message with name of room (global) and print result (room description).

        join_message = f'join {name}'
        client_socket.sendto(join_message.encode(), server)
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())

    # If the response is NOTOK then exit the program.
    else:
        print("There was an internal problem joining the server, exiting now...")
        sys.exit()

# Function to handle commands from the user, checking them over and sending to the server as needed.

def process_command(command):

    # Global variables
    global server
    global direction_list
    global room

    # Parse command.

    words = command.split()

    # Check if we are dropping something.  Only let server know if it is in our inventory.

    # Invalid drop command
    if (words[0] == 'drop'):
        if (len(words) != 2):
            print("Invalid command")
            return
        elif (words[1] not in inventory):
            print(f'You are not holding {words[1]}')
            return

    # Send command to server, if it isn't a local only one.

    if (command != 'inventory'):
        message = f'{command}'
        client_socket.sendto(message.encode(), server)

    # Check for particular commands of interest from the user.

    # Exit command

    if (command == 'exit'):
        # Drop every item in the player's inventory
        for item in inventory:
            message = f'drop {item}'
            client_socket.sendto(message.encode(), server)
        sys.exit(0)

    # Look command

    elif (command == 'look'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())

    # Inventory command

    elif (command == 'inventory'):
        # Print every item in the player's inventory
        print("You are holding:")
        if (len(inventory) == 0):
            print('  No items')
        else:
            for item in inventory:
                print(f'  {item}')

    # Take command

    elif (words[0] == 'take'):
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())
        words = response.decode().split()
        # Add the inventory to the users item if it was sucessfully removed from server.
        if ((len(words) == 2) and (words[1] == 'taken')):
            inventory.append(words[0])
    # Drop command

    elif (words[0] == 'drop'):
        # Remove the item from the inventory
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())
        inventory.remove(words[1])
    # Direction command

    elif (command in direction_list):

        # Get the URL and room name from the server.
        response, addr = client_socket.recvfrom(1024)
        new_room = response.decode()

        # Check if the command was valid then join the new room.

        if (new_room != 'NOTOK'):
            room = new_room
            join_room(room)

        # Command is not valid, notify user they cannot travle this way.

        else:
            print(f'You can not travel {command} from this room.')

    # Other commands/invalid commands.

    else:
        response, addr = client_socket.recvfrom(1024)
        print(response.decode())


# Function for reading input from the socket.

def socketReadFunction(input):
    # Try to get the response, if it timesout catch it and shut down the client.

    try:
        response, addr = client_socket.recvfrom(1024)

        # If the input coming is terminate then exit the program.

        if(response.decode() == 'terminate'):
            print('Disconnected from server ... exiting!')
            process_command('exit')
        # Print the response.

        print(response.decode())
    except socket.timeout:
        # Terminate the client.

        print('Server connection closed unexpectedly. Shutting down...')
        sys.exit(0)


# Function for reading terminal input.

def stdinReadFunction(input):
    line = sys.stdin.readline()[:-1]
    process_command(line)

# Our main function.

def main():
    # Global variables

    global name
    global client_socket
    global server

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    client_socket.settimeout(SOCKET_TIMEOUT)

    # Check command line arguments to retrieve a URL.

    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name for the player in the game")
    parser.add_argument("room", help="The name of the room the player wishes to join")
    args = parser.parse_args()

    # Set global variables to command line argument values.

    room = args.room
    name = args.name

    # Send message to enter the room.

    join_room(room)

    # Initializing selectors

    m_selector = selectors.DefaultSelector()
    m_selector.register(client_socket, selectors.EVENT_READ, socketReadFunction)
    m_selector.register(sys.stdin, selectors.EVENT_READ, stdinReadFunction)

    # We now loop forever, sending commands to the server and reporting results

    while True:
        do_prompt()
        # For loop checking over each selector so that we can have the correct callback depending on input stream

        for k, mask in m_selector.select():
            callback = k.data
            callback(k.fileobj)

if __name__ == '__main__':
    main()
