# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
import tasty_vk.apihelper as apihelper
from tasty_vk.utils import VKSession
from tasty_vk.constants import *

logger = logging.getLogger('tasty_vk')


class VK(apihelper.VKBase):
    def __init__(self, access_token=None, session_name=':memory:', ver=API_VERSION, captcha_handler=None):
        super().__init__(access_token, ver, captcha_handler)
        self.api = apihelper.VKMethod(self)
        self.session = VKSession(session_name)
        self.session.load()
        self.access_token = self.session['_'].get('access_token') or self.access_token
        self.session['_']['access_token'] = self.access_token
        self.session.save()
        self.longpoll = apihelper.VKLongpoll(self, None)
    
    def upload_document(self, path, peer_id=None, raw=False):
        return apihelper.upload_document(self, path, peer_id, raw)
    
    def upload_graffiti(self, path, peer_id=None, raw=False):
        return apihelper.upload_graffiti(self, path, peer_id, raw)
    
    def upload_voice(self, path, peer_id=None, raw=False):
        return apihelper.upload_voice(self, path, peer_id, raw)
    
    def upload_photo(self, path, peer_id=None, raw=False):
        return apihelper.upload_photo(self, path, peer_id, raw)
    
    def send_document(self, peer_id, path, **kwargs):
        return apihelper.send_document(self, peer_id, path, **kwargs)

    def send_graffiti(self, peer_id, path, **kwargs):
        return apihelper.send_graffiti(self, peer_id, path, **kwargs)

    def send_voice(self, peer_id, path, **kwargs):
        return apihelper.send_voice(self, peer_id, path, **kwargs)

    def send_photo(self, peer_id, paths, **kwargs):
        return apihelper.send_photo(self, peer_id, paths, **kwargs)
    
    def send_message(self, peer_id, message='', **kwargs):
        return apihelper.send_message(self, peer_id, message, **kwargs)

