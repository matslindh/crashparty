import pprint
import time

import wmi
import sys

from memorpy import (
    MemWorker
)

from flask import Flask
from flask_sse import sse


# Publish events as Server Sent Events through Flask SSE. Remove this and change the publish_event
# function to just a 'pass' for now if you don't want to use this.
app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

# Detect pid of server executable
c = wmi.WMI ()
pid = None

for process in c.Win32_Process(Name='Wreckfest.exe'):
    if 'server' in process.ExecutablePath:
        pid = process.ProcessId
        break

if not pid:
    sys.stderr.write("Unable to find pid of 'Wreckfest.exe' in 'server' directory.\n")
    sys.exit(-1)

mw = MemWorker(pid=pid)

print("Attached myself to pid " + str(pid))

# Memory address of the start of the scoring information. Can be found by using Cheat Engine to search for the
# nick that joined the server first.
locations = mw.mem_search(b'\x60\x00\x84\x00\xA2\x00\x88\x00\x7D\x00\x93\x00\x29\x00\x32\x00\x48\x00\x40\x00\x44\x00\x52\x00\x2E\x00\x4E\x00\x5A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
address_to_use = None

for location in locations:
    possible_address = mw.Address(location.value)
    possible_address += 40

    data = possible_address.read(maxlen=1, type='bytes')

    if 32 < data[0] < 125 or data[0] == 0:
        address_to_use = location.value

if not address_to_use:
    sys.stderr.write("Could not find possible memory address for players\n")
    sys.exit(-1)

address = mw.Address(address_to_use)

print("Using base address 0x" + format(address_to_use, 'x'))

statuses = {
    0: 'DISCONNECTED',
    2: 'READY',
    4: 'NOT_READY',
    6: 'RACING',
    9: 'RESULTS',
    18: 'CHANGING_CAR',
}

# This seemed promising until Panther RS and Warwagon had the same value.
# Leaving it in for now
cars = {
    40200: 'Starbeast',
    35300: 'Rocket',
    25100: 'Tristar',
    6000: 'Lawnmover',
    31600: 'Hammerhead',
    20500: 'Killerbee',
    28000: 'Gremlin',
    34000: 'Speedbird',
    21000: 'Boomer',
    38100: 'Roadslayer',
    37600: 'Rammer',
    39200: 'Roadcutter',
    42000: 'El Matador',
    22300: 'Bulldog',
    21600: 'Nexus RX',
    25500: 'Sunrise Super',
    39000: 'Speedemon',
    21300: 'Firefly',
    37000: 'Hotshot',
    51000: 'Muddigger',
    43000: 'Panther RS',
    38700: 'Dominator',
    43000: 'Warwagon',

    35977: 'Foo',
    31385: 'Foo',
    27298: 'Foo',
    23271: 'Foo',
}

players = []

# Initialize in memory player information structure
for player_no in range(0, 24):
    players.append({
        'last_lap_no': 0,
        'last_lap_time': None,
        'status': None,
        'status_str': '',
        'connected': False,
        'name': None,
        'rank': None,
        'health': None,
        'car': None,
    })


def publish_event(**kwargs):
    with app.app_context():
        sse.publish({
            **kwargs
        }, type='event')


while True:
    for player_no in range(0, 24):
        data = address.read(maxlen=192, type='bytes')
        address += 192
        status = data[90]

        if status != players[player_no]['status']:
            if players[player_no]['connected'] and players[player_no]['status'] is not None:
                print("new status, player " + str(player_no) + ', ' + str(status))

            if players[player_no]['status'] == 6:
                # After last lap the "previous lap" timer isn't being updated, but the timer for the current lap
                # stops running - so we fetch that value instead.
                last_lap = int.from_bytes(data[72:76].strip(b'\x00'), byteorder='little')
                lap_no = data[51]
                players[player_no]['last_lap_time'] = last_lap
                players[player_no]['last_lap_no'] = lap_no - 1
                publish_event(type='lap', player_no=player_no, player=players[player_no])
                print("FINISHED, LAST LAP TIME")
                pprint.pprint(players[player_no])

            players[player_no]['status'] = status

            if status in statuses:
                players[player_no]['status_str'] = statuses[status]
            else:
                print("unknown status code, " + str(status))

            publish_event(type='status', player_no=player_no, player=players[player_no])

        if not data[0]:
            if players[player_no]['connected']:
                print("Disconnected: " + str(players[player_no]['name']))
                publish_event(type='quit', player_no=player_no, player=players[player_no])

            players[player_no]['connected'] = False
            continue
        elif not players[player_no]['connected']:
            player = data[:data.index(b'\x00')].decode('iso-8859-1')
            players[player_no]['name'] = player
            print("player connected: " + str(player_no))
            players[player_no]['connected'] = True
            publish_event(type='join', player_no=player_no, player=players[player_no])

        player = data[:data.index(b'\x00')].decode('iso-8859-1')
        players[player_no]['name'] = player

        players[player_no]['ping'] = int.from_bytes(data[91:95].strip(b'\x00'), byteorder='little')
        last_lap = int.from_bytes(data[76:80].strip(b'\x00'), byteorder='little')
        lap_no = data[51]
        rank = data[47]
        health = data[46]
        car = int.from_bytes(data[88:90].strip(b'\x00'), byteorder='little')

        if players[player_no]['car'] != car:
            print("CHANGED CAR", player_no, car)
            players[player_no]['car'] = car

        if players[player_no]['status'] != 6:
            continue

        if players[player_no]['health'] != health:
            players[player_no]['health'] = health
            print("NEW HEALTH")
            pprint.pprint(players[player_no])

        if players[player_no]['rank'] != rank:
            players[player_no]['rank'] = rank
            print("NEW RANK")
            pprint.pprint(players[player_no])

            publish_event(type='rank', player_no=player_no, player=players[player_no])

        if lap_no < 2:
            continue

        if lap_no != players[player_no]['last_lap_no'] and players[player_no]['last_lap_time'] != last_lap:
            players[player_no]['last_lap_time'] = last_lap
            players[player_no]['last_lap_no'] = lap_no - 1

            print("NEW LAP")
            print("=======")

            pprint.pprint(players[player_no])
            publish_event(type='lap', player_no=player_no, player=players[player_no])

    # Scan the memory structure for changes twice each second
    time.sleep(0.5)
