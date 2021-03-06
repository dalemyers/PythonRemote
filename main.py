import json
import inspect

from Plugins import *
from Listeners import *
from Utilities import *
from StatusCode import *


class PycmoteServer(Plugin):  # We are also a plugin as we can then respond and act on server events

    id = "server"

    def __init__(self):
        """
        Creates a new instance of the server
        """
        Plugin.__init__(self)
        self.listener = None
        self.plugins = {}

    def set_listener(self, listener):
        """
        Sets the listener which we will later use to listen to remotes
        :param listener: A listener which will be used for listening to connections later
        :type listener: Listener
        """
        self.listener = listener

    def run_listener(self):
        """
        Informs the listener to begin listening
        :type self: PycmoteServer
        """
        self.listener.run(self.connection_formed, self.command_received)

    def run(self, callback, args):
        """
        Runs the command specified for this plugin
        :rtype : None
        :param callback: The function we will call with our success/failure information
        :param args: The data supplied from the remote to run the command
        """

        if "command" not in args.keys():
            callback(self, StatusCode.status_dict(StatusCode.UNSPECIFIED_COMMAND))

        if args["command"] == "quit":
            callback(self, StatusCode.status_dict(StatusCode.SUCCESS))
            self.listener.quit()
        else:
            callback(self, StatusCode.status_dict(StatusCode.UNSUPPORTED_COMMAND))

    def get_plugin(self, name):
        """Returns an instance of the plugin specified by the name passed in"""
        Logger().info("Plugin requested: " + name)

        # Load all plugins if we need to
        if self.plugins == {}:
            for k, v in globals().iteritems():
                # Get all subclasses of Plugin (but exclude Plugin itself and the server (which is always available)
                if inspect.isclass(v) and issubclass(v, Plugin) and Plugin != v and v.id != "server":
                    self.plugins[v.id] = {}
                    self.plugins[v.id]["activated"] = False
                    self.plugins[v.id]["plugin"] = v

                # Add the server
                self.plugins[self.id] = {"activated": True, "plugin": self}

        try:
            requested_plugin = self.plugins[name]
            if not requested_plugin["activated"]:
                requested_plugin["plugin"] = requested_plugin["plugin"]()
                requested_plugin["activated"] = True

            return requested_plugin["plugin"]
        except KeyError:
            Logger().info("Plugin '" + name + "' not found.")
            return None

    def command_received(self, json_data):
        """Called when a command is received. It parses the json and calls the correct plugin passing in the data."""
        try:
            data = json.loads(json_data)
        except ValueError:
            Logger().error("Invalid JSON string: " + json_data)
            # No point in going any further
            self.callback(self, StatusCode.status_dict(StatusCode.INVALID_JSON))
            return
        Logger().info("Parsed: " + str(data))
        if 'type' not in data.keys():
            Logger().warning("No 'type' key was found in the command. Assuming sync")
            data['type'] = 'sync'
        if not valid_json(data):
            Logger().error("Command was not valid")
            self.callback(self, StatusCode.status_dict(StatusCode.INVALID_JSON))
            return

        plugin = self.get_plugin(data["name"])

        if plugin is None:
            self.callback(self, StatusCode.status_dict(StatusCode.PLUGIN_NOT_FOUND))
            Logger().error("Plugin '" + data["name"] + "' not found")

        try:
            plugin.run(self.callback, data['data'])
        except Exception, e:
            status_dict = StatusCode.status_dict(StatusCode.PLUGIN_ERROR_UNKNOWN)
            status_dict["further_info"] = str(e.__class__) + ": " + str(e)
            self.callback(plugin, StatusCode.status_dict(StatusCode.PLUGIN_ERROR_UNKNOWN))
            Logger().error("Plugin run failed: " + str(e.__class__) + ': ' + str(e))

    def connection_formed(self):
        """Called when a new connection is formed."""
        self.callback(self, StatusCode.status_dict(StatusCode.CONNECTION_FORMED))
        Logger().info("Client connection")

    def callback(self, plugin, status, values=None):
        """The callback method provided to the plugin so that the response can be issued."""
        if values is None:
            values = ""
        if type(plugin) == str:
            self.listener.send_response({"plugin": plugin, "status": status, "values": values})
        else:
            self.listener.send_response({"plugin": plugin.id, "status": status, "values": values})


def main():
    """Main method which loads a listener and starts it"""
    server = PycmoteServer()
    socket_port = 22000
    if len(sys.argv) > 1:
        if sys.argv[1] == 'socket':
            Logger().info('Creating SocketListener()')
            server.set_listener(SocketListener(socket_port))
        elif sys.argv[1] == 'ssh':
            Logger().info('Creating SSHListener()')
            server.set_listener(SSHListener())
        else:
            Logger().error('Invalid listener. Quitting.')
            sys.exit(1)
    else:
        Logger().warning('No argument specified, defaulting to SocketListener()')
        server.set_listener(SocketListener(socket_port))

    while True:
        # We want this to start running again should it fail
        try:
            Logger().info("Running listener")
            server.run_listener()
            Logger().info("Listener completed its task. Running again.")
        except Exception, e:
            Logger().error('Listener failed: ' + str(e))
            traceback.print_exc()
        # TODO: Remove later
        sys.exit(0)


if __name__ == '__main__':
    main()
