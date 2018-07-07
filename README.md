Crashparty - A memory monitor for Wreckfest servers
---------------------------------------------------

This is no way affiliated with Wreckfest, Bugbear Entertainment or THQ Nordic.

Motivation
==========

When Flatout 2 was popular we had our own internal scoring system that kept track of our own Flatout 2 records, scoring
and tournaments. Since Wreckfest doesn't have the same support for exporting game results after finishing a race, a
different strategy had to be used.

Solution
========

The easy solution would be for the Wreckfest server to have a verbose logging format that logged all events to the
server log, allowing our monitor to tail the server log file and parse the events as they happen. The executable does
however not support that (.. and I weren't able to find any hidden support for it either).

Instead we're now parsing the structure describing the current state of the game, and detecting changes to "last lap"
times, car selections and player status ("Selecting car", etc.). This is not perfect by any means, but it actually
works.

State of the project
====================

It's hacky. It's in progress. It's not very user friendly (if at all).

It does nothing more than promised (if even that), and it's hard to get it to work. You currently have to give it the
process id (pid) of the Wreckfest server manually, and use Cheat Engine (or a similiar memory scanner) to find the
location of where the information structure starts in memory. Insert the values into `monitor.py` before running it.

Another issue is that the project uses memorpy, and the current source version of memorpy doesn't run under Python 3.
To fix this I've patched memorpy to be Python 3 compatible under Windows. This pull request can be found here:

https://github.com/n1nj4sec/memorpy/pull/20

Unless these patches has been applied to the main memorpy tree, you'll have to check out my branch and install it
manually with pip in your virtual environment to get a memorpy version that supports Python 3.

The current version also depend on flask_sse (and thus Redis) to push Server Sent Events to a web frontend that shows
the current state of the game. This web frontend is not implemented except for outputting log data when an event occurs.

License
=======

The MIT License.