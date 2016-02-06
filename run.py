import logging, time
from yowsup.layers import YowLayerEvent, YowParallelLayer
from yowsup.layers.auth import AuthError
from yowsup.layers.network import YowNetworkLayer
from yowsup.stacks.yowstack import YowStackBuilder

from layer import EchoLayer

CREDENT = ("919643392110", "68K8YZb/XHW5ZA1KxL23MMsfHBc=") # replace with your phone and password
class YowsupEchoStack(object):
    def __init__(self, credentials):
        "Creates the stacks of the Yowsup Server,"
        self.credentials = credentials
        stack_builder = YowStackBuilder().pushDefaultLayers(True)

        # on the top stack, the two layers that controls the bot and respond to messages and notifications
        # see both of classes for more documentation
        stack_builder.push(YowParallelLayer([EchoLayer]))
        self.stack = stack_builder.build()
        self.stack.setCredentials(credentials)

    def start(self):
        "Starts the connection with Whatsapp servers,"
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            logging.info("#" * 50)
            logging.info("\tServer started. Phone number: %s" % self.credentials[0])
            logging.info("#" * 50)
            self.stack.loop(timeout=0.5, discrete=0.5)
        except AuthError as e:
            logging.exception("Authentication Error: %s" % e.message)
        except Exception as e:
            logging.exception("Unexpected Exception: %s" % e.message)


if __name__ == "__main__":
    import sys
    log_format = '_%(filename)s_\t[%(levelname)s][%(asctime)-15s] %(message)s'
    logging_level = logging.INFO
    logging.basicConfig(stream=sys.stdout, level=logging_level, format=log_format)
    server = YowsupEchoStack(CREDENT)
    while True:
        # In case of disconnect, keeps connecting...
        server.start()
        logging.info("Restarting..")
