__author__ = 'h_hack'

from yowsup.layers.protocol_media.mediauploader import MediaUploader
from yowsup.layers.protocol_media.protocolentities.iq_requestupload import RequestUploadIqProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable import \
    DownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_image import \
    ImageDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_video import \
    VideoDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_audio import \
    AudioDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
import subprocess
import os
import logging
import hashlib
import re

class MediaSender():
    """
        This is a superclass that does the job of download/upload a media type.
        The classes bellow extends it and are used by the views.
    """

    def __init__(self, interface_layer):
        """
            The construction method receives the interface_layer (RouteLayer), so it can access the protocol methods
            to upload and send the media files
        """
        self.interface_layer = interface_layer
        self.storage_path = "/tmp/"
        self.file_extension_regex = re.compile("^.*\.([0-9a-z]+)(?:[\?\/][^\s]*)?$")
        self.MEDIA_TYPE = None
        self.path=None
        self.jid=None

    def send_by_path(self, jid, path, caption=None):
        """
            Send a file by its absolute path.

            Creates a RequestUpload entity, that will verify if the media has already been uploaded.
            Then calls the _on_upload_result.
        """
        self.jid=jid
        self.path=path
        entity = RequestUploadIqProtocolEntity(self.MEDIA_TYPE, filePath=self.path)
        self.interface_layer._sendIq(entity,self._on_upload_result,self._on_error)


    def _on_upload_result(self,upload_result, requestUploadIqProtocolEntity, caption=None):
        """
            If the file has never been uploaded, will be uploaded and then call the _do_send_file
        """
        if upload_result.isDuplicate():
            self._do_send_file(self.path, upload_result.getUrl(), self.jid, upload_result.getIp(), caption)
        else:
            callback = lambda file_path, jid, url: self._do_send_file(self.path, url, self.jid, upload_result.getIp(),
                                                                      caption)
            mediaUploader = MediaUploader(self.jid, self.interface_layer.getOwnJid(),self.path,
                                          upload_result.getUrl(),
                                          upload_result.getResumeOffset(),
                                          callback, self._on_error, self._on_upload_progress, async=True)
            mediaUploader.start()

    def _do_send_file(self, file_path, url, to, ip=None, caption=None):
        """
            Now the media file has been uploaded and the whatsapp server returns a media_path.
            The media_path is then sent to the receipt.
        """
        entity = None
        if self.MEDIA_TYPE == DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_VIDEO:
            entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, self.MEDIA_TYPE, ip, to)
        elif self.MEDIA_TYPE == DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_IMAGE:
            entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to, caption=caption)
        elif self.MEDIA_TYPE == DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_AUDIO:
            entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to)
        self.interface_layer.toLower(entity)

    def _on_upload_progress(self, filePath, jid, url, progress):
        if progress % 50 == 0:
            logging.info("[Upload progress]%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))

    def _on_error(self, jid, *args, **kwargs):
        self.interface_layer.toLower(TextMessageProtocolEntity("{!}", to=jid))


class mediaview(MediaSender):

    def __init__(self,interface_layer):
        MediaSender.__init__(self, interface_layer)
        self.MEDIA_TYPE = RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO

    def send(self, jid, text, lang='en'):
        text = text.replace("'", '"')
        try:
            file_path = self.tts_record(text, lang)
            self.send_by_path(jid, file_path)
        except Exception as e:
            logging.exception(e)
            self._on_error(jid)

    def tts_record(self, text, lang='en'):
        id = hashlib.md5(text).hexdigest()
        file_path= ''.join([self.storage_path, id, ".wav"])
        cmd = "espeak -v%s -w %s '%s'" % (lang, file_path, text)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait()
        return file_path



    def callback(self,inmessageprotocolentity):
        self.send(jid=inmessageprotocolentity.getFrom(), text= inmessageprotocolentity.getBody())