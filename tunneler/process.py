"""
Tunnel process management code.
"""

import re
from subprocess import call

import psutil

from .models import Tunnel

PORT_MATCHER = re.compile(r'.*-L(\d+):localhost:(\d+).*')
LOGIN_MATCHER = re.compile(r'.* ([^@]+)@([^ ]+).*')

# -g allow remote host to connect to local port
# -f go to background
# -o StrictHostKeyChecking=no
START_COMMAND = \
    'ssh -g -f -N -L{local_port}:localhost:{remote_port} {user}@{server}'


class ProcessHelper(object):
    """
    Class that offers helper functions for working with tunnel processes.
    """

    def get_active_tunnels(self):
        """
        Identify all running tunnels and return their data.

        Yield Tunnels
        """
        for process in psutil.process_iter():
            try:
                if process.name() == 'ssh' and '-N' in process.cmdline():
                    try:
                        command = ' '.join(process.cmdline())
                        local_port, remote_port, user, server = \
                            self.extract_tunnel_info(command)
                    except AttributeError:
                        pass
                    else:
                        yield Tunnel(
                            'unidentified',
                            process,
                            local_port,
                            remote_port,
                            user,
                            server,
                        )
            except psutil.AccessDenied:
                pass

    def extract_tunnel_info(self, line):
        """
        Get useful tunnel process information from its launch command.

        Return local port, remote port, user, server
        """
        (local_port, remote_port) = PORT_MATCHER.match(line).groups()
        (user, server) = LOGIN_MATCHER.match(line).groups()

        return int(local_port), int(remote_port), user, server

    def start_tunnel(self, user, server, local_port, remote_port):
        """
        Launch a tunnel based on the specified parameters.

        Return boolean with result of call.
        """
        command = START_COMMAND.format(
            user=user,
            server=server,
            local_port=local_port,
            remote_port=remote_port
        )
        return call(command.split()) == 0

    def stop_tunnel(self, tunnel):
        """
        Terminate a tunnel's process.

        Return boolean with result of operation.
        """
        try:
            tunnel.process.terminate()
            return True
        except:
            return False
