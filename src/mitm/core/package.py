#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Handle the package coming from the source and send to the destination. In the middle of this task the packages
can modify as you wish.

This code is partially taken bye LiveOverflow/PwnAdventure3 (https://github.com/LiveOverflow/PwnAdventure3) under the
GPL-3.0 License
"""
from importlib import reload
from logging import debug
from socket import socket
from sys import exc_info
from traceback import format_exception

import core.parser
from core.hack import Hack
from core.inject import Inject
from core.queue import Queue


class Package:
    """
    Manage the packages. It could be receive, send and inject.
    """

    def __init__(self, is_server: bool, source: socket, destination: socket, port: int) -> None:
        """
        Constructor which init the class.

        :type is_server: bool
        :param is_server: True means that it is sending packages from the Client to the Server. Otherwise it is false.

        :type source: socket
        :param source: Object with the source connection.

        :type destination: socket
        :param destination: Object with the destination connection.

        :type port: int
        :param port: The number of the port for the communication.

        :rtype: Package
        :return: The object instanced of this class.
        """
        self.running = True
        self.is_server = is_server
        self.source = source
        self.destination = destination
        self.port = port

    def terminate(self) -> None:
        """
        Stop the execution.

        :rtype: None
        """
        self.running = False

    def start(self) -> None:
        """
        Handle the packages.

        :rtype: None
        """
        if self.is_server:
            source = 'server'
            destination = 'client'
            queue = Queue.CLIENT_QUEUE
        else:
            source = 'client'
            destination = 'server'
            queue = Queue.SERVER_QUEUE

        inject = Inject()

        while self.running:
            data: bytes = self.source.recv(4096)
            if data:
                try:
                    data = inject.run(data, destination)

                    if len(Queue.HACKS):
                        target, retries = Queue.HACKS.pop(0)
                        if target.lower() == Hack.fire_balls.lower():
                            inject.get_fire_balls(retries)

                    if len(queue) > 0:
                        packet: bytes = queue.pop(0)
                        message = f'--*-- Send to {destination}: {packet.hex()}'
                        print(message)
                        debug(message)
                        self.destination.sendall(packet)

                    reload(core.parser)
                    parse = core.parser.Parse(data)

                    if self.is_server:
                        parse.server(self.port)
                    else:
                        parse.client(self.port)

                except Exception as e:
                    error_type, value, traceback = exc_info()
                    message = f'ERROR: {source}[{self.port}]: {e}\n' \
                              f'{"".join(format_exception(error_type, value, traceback))}' \
                              f'  -> {data.hex()}\n' \
                              f'\n\n'
                    print(message)
                    debug(message)
                self.destination.sendall(data)
        self.source.close()
