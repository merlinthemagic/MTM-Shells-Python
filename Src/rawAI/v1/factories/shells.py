"""
MTM_Shells/factories/shells.py

Mirrors MTM-SSH's Factories/Shells.php: the object that actually knows how
to build and authenticate a connection, handed out by Factories.get_shells().
"""

from MTM_Shells.tools.connection import RouterOSConnection


class Shells:
    """Mirrors MTM-SSH's Factories\\Shells.php."""

    def password_authentication(self, host, username, password, ctrl_obj=None,
                                 port=22, connect_timeout=30.0, debug_log=None):
        """
        Connect to a RouterOS device with password auth and return an
        already-connected RouterOSConnection, ready for get_cmd()/exec().

        Mirrors $ctrlObj = Factories::getShells()->passwordAuthentication(
            $ip, $user, $pass, $ctrlObj, $port, $timeout
        );

        `ctrl_obj` is accepted for signature-parity with the PHP version,
        which allows chaining a new authentication onto an *existing* open
        shell (e.g. SSH to host A, then from that shell SSH to host B).
        That chaining/"Destination" behavior isn't ported here -- only
        fresh, direct connections are supported -- so passing a value
        other than None raises.
        """
        if ctrl_obj is not None:
            raise NotImplementedError(
                "Chaining onto an existing shell/connection (the PHP "
                "library's 'Destination' feature) isn't implemented in "
                "this port -- only direct, fresh connections are."
            )
        conn = RouterOSConnection(
            host, username, password, port=port,
            connect_timeout=connect_timeout, debug_log=debug_log,
        )
        conn.connect()
        return conn
