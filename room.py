# Import Statements.

import socket
import signal
import sys
import argparse

# Discovery server constant

DISCOVERY_SERVER = ('localhost', 8000)

# Saved information on the room.

name = ''
description = ''
items = []
rooms = {}
room_socket = None

# Direction List.

direction_list = ['north', 'south', 'west', 'east', 'up', 'down']


# List of clients currently in the room.

client_list = []

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')

    # Send the terminate command to each client in the client list.

    for client in client_list:
        room_socket.sendto('terminate'.encode(), client[1])

    # Deregister from the discovery service and exit.

    deregister_message = f'DEREGISTER {name}'
    room_socket.sendto(deregister_message.encode(), DISCOVERY_SERVER)
    sys.exit(0)

# Search the client list for a particular player.

def client_search(player):
    for reg in client_list:
        if reg[0] == player:
            return reg[1]
    return None

# Search the client list for a particular player by their address.

def client_search_by_address(address):
    for reg in client_list:
        if reg[1] == address:
            return reg[0]
    return None

# Add a player to the client list.

def client_add(player, address):
    registration = (player, address)
    client_list.append(registration)

# Remove a client when disconnected.

def client_remove(player):
    for reg in client_list:
        if reg[0] == player:
            client_list.remove(reg)
            break

# Summarize the room into text.

def summarize_room(addr):

    # Global variables.

    global name
    global description
    global items

    # Pack description into a string and return it.

    summary = name + '\n\n' + description + '\n\n'
    # If there is no items or other players in the room
    if len(items) + (len(client_list) - 1) == 0:
        summary += "The room is empty.\n"

    # If there is 1 item in the room.
    elif len(items) == 1:
        summary += "In this room, there is:\n"
        summary += f'  {items[0]}\n'

    # If there is more than 1 item in the room.
    else:
        summary += f'In this room, there are {len(items)} items:\n'
        for item in items:
            summary += f'  {item}\n'

    # If there is no other players in the room.
    if (len(client_list) - 1) <= 0:
        summary += 'In this room, there are no other players.\n'
    # If there is 1 other player in the room.
    elif (len(client_list) - 1) == 1:
        summary += "In this room, there is one other player:\n"
        for client in client_list:
            if client[1] != addr:
                summary += f'  {client[0]}\n'
    # If there is more than one other player in the room.
    else:
        summary += f'In this room, there are {len(client_list) - 1} other players:\n'
        for client in client_list:
            if client[1] != addr:
                summary += f'  {client[0]}\n'

    # Return the room summary.
    return summary

# Print a room's description.

def print_room_summary(addr=0):
    print(summarize_room(addr)[:-1])

# Process incoming message.

def process_message(message, addr):

    # Parse the message.

    words = message.split()

    # If player is joining the server, add them to the list of players.

    if (words[0] == 'join'):
        if (len(words) == 2):

            # Add the client to the client list.

            client_add(words[1],addr)

            print(f'User {words[1]} joined from address {addr}')

            # Send a message to every other client notifying them that a client joined the room.

            for client in client_list:
                if client[1] != addr:
                    join_message = f'{words[1]} entered the room.'
                    room_socket.sendto(join_message.encode(), client[1])
            return summarize_room(addr)[:-1]
        else:
            return "Invalid command"

    # If player is leaving the server. remove them from the list of players.

    elif (message == 'exit'):
        # For each other player in the room notify them of the player leaving.
        for client in client_list:
            if client[1] != addr:
                exit_message = f'{client_search_by_address(addr)} left the game.'
                room_socket.sendto(exit_message.encode(), client[1])
        # Remove the client from the list.
        client_remove(client_search_by_address(addr))
        return 'Goodbye'


    # If player looks around, give them the room summary.

    elif (message == 'look'):
        return summarize_room(addr)[:-1]

    # If player takes an item, make sure it is here and give it to the player.

    elif (words[0] == 'take'):
        if (len(words) == 2):
            # Remove the item from the room's item list.
            if (words[1] in items):
                items.remove(words[1])
                return f'{words[1]} taken'
            else:
                return f'{words[1]} cannot be taken in this room'
        else:
            return "Invalid command"

    # If player drops an item, put in in the list of things here.

    elif (words[0] == 'drop'):
        if (len(words) == 2):
            # Add the dropped item to the room's item list.
            items.append(words[1])
            return f'{words[1]} dropped'
        else:
            return "Invalid command"

    # If the player wants to travel to a different room.

    elif (words[0] in direction_list and len(words) == 1):
        if words[0] in rooms:
            # Get the room name from the rooms array.
            room_name = rooms[words[0]]

            # Remove the leaving client from the client list

            leaving_client = client_search_by_address(addr)
            client_remove(client_search_by_address(addr))

            # Send a message to each other player in the room the direction the player is going.

            for client in client_list:
                leaving_message = f'{leaving_client} left the room, heading {words[0]}.'
                room_socket.sendto(leaving_message.encode(), client[1])

            # Return the room name to be interpreted by the player.

            return f'{room_name}'
        else:
            return 'NOTOK'

    # If the player wants to say something.

    elif ('say' in message):
        # If the message is just say with no words ask them to try again.
        if message.strip() == 'say':
            return "What did you want to say?"
        message_text = message.split(" ", 1)[1]
        chat_message = f'{client_search_by_address(addr)} said "{message_text}".'

        # Send the message to every other client in the room.
        for client in client_list:
            if client[1] != addr:
                room_socket.sendto(chat_message.encode(), client[1])
        # Return to the player what they said.
        return f'You said "{message_text}".'

    elif (message == 'SERVER TERMINATE'):
        print('Discovery service shutdown, terminating server now...')

        # Send the terminate command to each client in the client list.

        for client in client_list:
            room_socket.sendto('terminate'.encode(), client[1])

        # Shutdown the server
        sys.exit(0)

    # Otherwise, the command is bad.

    else:
        return "Invalid command"

def register_server(url, name):
    command = f'REGISTER {url} {name}'
    room_socket.sendto(command.encode(), DISCOVERY_SERVER)
    message, addr = room_socket.recvfrom(1024)
    words = message.decode().split()
    if(words[0] == "NOTOK"):
        print(message)
        for client in client_list:
            room_socket.sendto('terminate'.encode(), client[1])
        sys.exit(0)

# Our main function.

def main():

    # Global variables

    global name
    global description
    global items
    global room_socket
    global rooms

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments for room settings.

    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name of the room")
    parser.add_argument("description", help="description of the room")
    parser.add_argument("item", nargs='*', help="list of items in the room")
    parser.add_argument("-n", "--north", help="room name down north")
    parser.add_argument("-w", "--west", help="room name down west")
    parser.add_argument("-s", "--south", help="room name down south")
    parser.add_argument("-e", "--east", help="room name down east")
    parser.add_argument("-u", "--up", help="room name down up")
    parser.add_argument("-d", "--down", help="room name down")
    args = parser.parse_args()

    name = args.name
    description = args.description
    items = args.item

    # Setup rooms that can be travelled to depending on which direction args are added.

    if args.north:
        rooms['north'] = args.north
    if args.south:
        rooms['south'] = args.south
    if args.west:
        rooms['west'] = args.west
    if args.east:
        rooms['east'] = args.east
    if args.up:
        rooms['up'] = args.up
    if args.down:
        rooms['down'] = args.down

    # Report initial room state.
    print('Room Starting Description:\n')
    print_room_summary()


    # Create the socket.  We will ask this to work on any interface and to use
    # the port given at the command line.  We'll print this out for clients to use.

    room_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    room_socket.bind(('', 0))

    # Register server with discovery service

    url = f'room://localhost:{room_socket.getsockname()[1]}'
    register_server(url, name)

    print('\nRoom will wait for players at port: ' + str(room_socket.getsockname()[1]))

    # Loop forever waiting for messages from clients.

    while True:

        # Receive a packet from a client and process it.

        message, addr = room_socket.recvfrom(1024)

        # Process the message and retrieve a response.

        response = process_message(message.decode(), addr)

        # Send the response message back to the client.

        room_socket.sendto(response.encode(),addr)


if __name__ == '__main__':
    main()
