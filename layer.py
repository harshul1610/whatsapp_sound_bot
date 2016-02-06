__author__ = 'h_hack'


from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
import threading
import logging
from media import mediaview

class EchoLayer(YowInterfaceLayer):


    @ProtocolEntityCallback("message")
    def onMessage(self, inmessageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over

        if True:
            receipt = OutgoingReceiptProtocolEntity(inmessageProtocolEntity.getId(), inmessageProtocolEntity.getFrom(),
                                                    'read', inmessageProtocolEntity.getParticipant())

            mediaobj=mediaview(self)

            if inmessageProtocolEntity.getType()=='text':
                threading.Thread(target=self.handle_callback, args=(mediaobj.callback,inmessageProtocolEntity)).start()

            self.toLower(receipt)


    def handle_callback(self,callback,inmessageProtocolEntity):
        try:
            data = callback(inmessageProtocolEntity)
            if data:
                self.toLower(data)
        except Exception as e:
            logging.exception("error routing message")

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        self.toLower(ack)
