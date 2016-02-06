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
import time
import os
import logging
import requests
import shutil
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

    def send_by_url(self, jid, file_url, caption=None):
        """ Downloads and send a file_url """
        try:
            # self.interface_layer.toLower(TextMessageProtocolEntity("{...}", to=jid))
            file_path = self._download_file(file_url)
            self.send_by_path(jid, file_path, caption)
        except Exception as e:
            logging.exception(e)
            self._on_error(jid)

    def send_by_path(self, jid, path, caption=None):
        """
            Send a file by its absolute path.

            Creates a RequestUpload entity, that will verify if the media has already been uploaded.
            Then calls the _on_upload_result.
        """
        entity = RequestUploadIqProtocolEntity(self.MEDIA_TYPE, filePath=path)
        success_callback = lambda successEntity, originalEntity: self._on_upload_result(jid, path, successEntity,
                                                                                        originalEntity, caption)
        err_callback = lambda errorEntity, originalEntity: self._on_error(jid)
        self.interface_layer._sendIq(entity, success_callback, err_callback)

    def _download_file(self, file_url):
        """
            This method check for duplicate file before downloading,
            If not downloaded, download it, saves locally and returns the path
        """
        file_path = self._build_file_path(file_url)
        if not os.path.isfile(file_path):
            response = requests.get(file_url, stream=True)
            with open(file_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
        return file_path

    def _on_upload_result(self, jid, file_path, upload_result, requestUploadIqProtocolEntity, caption=None):
        """
            If the file has never been uploaded, will be uploaded and then call the _do_send_file
        """
        if upload_result.isDuplicate():
            self._do_send_file(file_path, upload_result.getUrl(), jid, upload_result.getIp(), caption)
        else:
            callback = lambda file_path, jid, url: self._do_send_file(file_path, url, jid, upload_result.getIp(),
                                                                      caption)
            mediaUploader = MediaUploader(jid, self.interface_layer.getOwnJid(), file_path,
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

    def _get_file_ext(self, url):
        return self.file_extension_regex.findall(url)[0]

    def _build_file_path(self, url):
        id = hashlib.md5(url).hexdigest()
        return ''.join([self.storage_path, id, ".", self._get_file_ext(url)])


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
        file_path = self._build_file_path(text)
        cmd = "espeak -v%s -w %s '%s'" % (lang, file_path, text)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait()
        return file_path

    def _build_file_path(self, text):
        id = hashlib.md5(text).hexdigest()
        return ''.join([self.storage_path, id, ".wav"])

    def callback(self,inmessageprotocolentity):
        self.send(jid=inmessageprotocolentity.getFrom(), text= inmessageprotocolentity.getBody())