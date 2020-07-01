# -*- coding: utf-8 -*-
import logging
import random
import time

from requests import get, post, ReadTimeout
from tasty_vk.utils import RDict, ApiException, ParseError, LongpollException
from tasty_vk.constants import *

logger = logging.getLogger('tasty_vk')


class VKMethod:
    def __init__(self, master, chain=None):
        self.master = master
        self.chain = chain or []

    def __getattr__(self, method):
        return VKMethod(self.master, self.chain + [method])

    def __call__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(o) for o in v)

        return self.master.call('.'.join(self.chain), **kwargs)


class VKBase:
    def __init__(self, access_token=None, ver=API_VERSION, captcha_handler=None):
        self.access_token = access_token
        self.version = ver
        self.captcha_handler = captcha_handler

    def call(self, method, **params):
        raw = params.pop('_raw') if '_raw' in params else False
        attempt = params.pop('_attempt') if '_attempt' in params else 0
        use_post = params.pop('_post') if '_post' in params else False
        backup = params.copy()
        for k, v in params.items():
            if isinstance(v, (list, tuple)):
                params[k] = ','.join(str(o) for o in v)

        if self.access_token is not None:
            logger.debug('%s%r', method, params)
            params['access_token'] = self.access_token
        else:
            logger.debug('anon/%s%r', method, params)

        if 'v' not in params:
            params['v'] = self.version

        try:
            if use_post:
                request = post(API_URL % method, data=params)
            else:
                request = get(API_URL % method, params=params)
        except Exception as e:
            logger.error('exception during connection: %r', e)
            if attempt > 10:
                raise e
            time.sleep(1)
            return self.call(method, **backup, _attempt=attempt+1)

        try:
            response = request.json()
        except ValueError as e:
            logger.error('exception during parsing: %r', e)
            raise ParseError(e, request)

        if 'error' in response:
            error = response['error']
            message = 'Error {error_code}: {error_msg}'.format(**error)
            logger.error(message)
            response = self.error_handler(method, backup,
                                          response, _attempt)
            if not response:
                raise ApiException(message, backup, response)

        logger.debug('response = %r', response)
        return response if raw else RDict.convert(response['response'])

    def error_handler(method, params, response, attempt):
        error = response['error']
        code = error['error_code']
        if attempt > 10:
            return
        if code in (1, 10):  # Unknown error / Internal Server error
            time.sleep(1)
            return self.call(method, **params, _attempt=attempt + 1)
        elif code == 14 and callable(self.captcha_handler):
            captcha_sid = error['captcha_sid']
            captcha_img = error['captcha_img']
            result = self.captcha_handler(captcha_sid, captcha_img)
            if not result:
                return
            params['captcha_sid'] = captcha_sid
            params['captcha_key'] = result
            return self.call(method, **params, _attempt=attempt + 1)

    @staticmethod
    def post(url, **params):
        logger.debug('post/%s%r', params)

        try:
            request = post(url, **params)
        except Exception as e:
            logger.error('exception during connection: %r', e)
            raise e

        try:
            response = request.json()
        except ValueError as e:
            logger.error('exception during parsing: %r', e)
            raise ParseError(e, request)

        if 'error' in response:
            message = 'Error: %r', response['error']
            logger.error(message)
            raise ApiException(message, params, response)

        logger.debug('response = %r', response)
        return RDict.convert(response)


def send_message(self, peer_id, message='', **kwargs):
    attachments = [str(v) for v in kwargs.get('attachments', [])]
    forwarded = [str(v) for v in kwargs.get('fwd_messages', [])]
    return self.call('messages.send',
                     peer_id=peer_id,
                     message=message,
                     random_id=random.randint(-0x7fffffff, 0xffffffff),
                     attachment=','.join(attachments),
                     forward_messages=forwarded, **kwargs,
                     _post=True)


def upload_document(self, path, peer_id=None, raw=False):
    server = self.call('docs.getMessagesUploadServer', peer_id=peer_id)
    doc = VKBase.post(server.upload_url, files=dict(file=open(path, 'rb')))
    document = self.call('docs.save', file=doc.file, title=path)
    if 'doc' in document:
        if raw:
            return document['doc']
        return 'doc{owner_id}_{id}'.format(**document.doc.__dict__)
    else:
        if raw:
            return document[0]
        return 'doc{owner_id}_{id}'.format(**document[0].__dict__)


def send_document(self, peer_id, path, **kwargs):
    document = self.upload_document(path, peer_id)
    return send_message(self, peer_id, attachments=[document], **kwargs)


def upload_graffiti(self, path, peer_id=None, raw=False):
    server = self.call('docs.getMessagesUploadServer',
                       type='graffiti', peer_id=peer_id)
    doc = VKBase.post(server.upload_url, files=dict(file=open(path, 'rb')))
    document = self.call('docs.save', file=doc.file, title='graffiti.png')
    if 'doc' in document:
        if raw:
            return document['doc']
        return 'doc{owner_id}_{id}'.format(**document.doc.__dict__)
    else:
        if raw:
            return document[0]
        return 'doc{owner_id}_{id}'.format(**document[0].__dict__)


def send_graffiti(self, peer_id, path, **kwargs):
    graffiti = self.upload_graffiti(path, peer_id)
    return send_message(self, peer_id, attachments=[graffiti], **kwargs)


def upload_voice(self, path, peer_id=None, raw=False):
    server = self.call('docs.getMessagesUploadServer',
                       type='audio_message', peer_id=peer_id)
    doc = VKBase.post(server.upload_url, files=dict(file=open(path, 'rb')))
    document = self.call('docs.save', file=doc.file, title=path)
    if raw:
        return document['audio_message']
    return 'doc{owner_id}_{id}'.format(**document.audio_message.__dict__)


def send_voice(self, peer_id, path, **kwargs):
    voice = self.upload_voice(path, peer_id)
    return send_message(self, peer_id, attachments=[voice], **kwargs)


def upload_photo(self, path, peer_id=None, raw=False):
    server = self.call('photos.getMessagesUploadServer', peer_id=peer_id)
    photo_info = VKBase.post(server.upload_url,
                             files=dict(photo=open(path, 'rb')))
    photo = self.call('photos.saveMessagesPhoto', **photo_info.__dict__)
    if 'photo' in photo:
        if raw:
            return photo['photo']
        return 'photo{owner_id}_{id}'.format(**photo.photo.__dict__)
    else:
        if raw:
            return photo[0]
        return 'photo{owner_id}_{id}'.format(**photo[0].__dict__)


def send_photo(self, peer_id, paths, **kwargs):
    photos = []
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        photos.append(self.upload_photo(path, peer_id))
    return send_message(self, peer_id, attachments=photos, **kwargs)


class VKLongpoll:
    def __init__(self, master,
                       group_id=None,
                       server=None,
                       ts=None,
                       key=None,
                       reconnect=True,
                       raw=False):
        self._polling = False
        self.master = master

        lp_data = master.session.get('lp', {})
        self.group_id = group_id or lp_data.get('group_id')
        self.server = server or lp_data.get('server')
        self.ts = ts or lp_data.get('ts')
        self.key = key or lp_data.get('key')
        self.reconnect = reconnect
        self.raw = raw

    def get_events(self):
        server_url = self.server
        if 'https' not in server_url:
            server_url = 'https://' + server_url

        try:
            request = get(server_url, params={
                'act': 'a_check',
                'key': self.key,
                'ts': self.ts,
                'wait': 25,
                'mode': 255,
                'version': LP_VERSION
            }, timeout=30)
        except (ConnectionError, ReadTimeout) as e:
            exception_type = type(e).__name__
            logger.error('%s occurred while fetching: %r', exception_type, e)
            if self.reconnect:
                time.sleep(1)
                return self.get_events()
            else:
                raise e

        try:
            data = request.json()
        except ValueError as e:
            raise ParseError(e, request)

        return data

    def get_longpoll_server(self):
        if self.group_id is None:
            server = self.master.call('messages.getLongPollServer',
                                      lp_version=LP_VERSION)
        else:
            server = self.master.call('groups.getLongPollServer',
                                      lp_version=LP_VERSION,
                                      group_id=self.group_id)
        self.server = server['server']
        self.ts = server['ts']
        self.key = server['key']

    def update_session(self):
        if 'lp' not in self.master.session:
            self.master.session['lp'] = {}
        self.master.session['lp'].update({
            'group_id': self.group_id,
            'server': self.server,
            'ts': self.ts,
            'key': self.key
        })
        self.master.session.save()

    def poll_events(self):
        if self.server is None:
            self.get_longpoll_server()
        self._polling = True
        while self._polling:
            data = self.get_events()
            if 'failed' in data:
                code = data['failed']
                if code == 1:
                    old_ts = self.ts
                    self.ts = data['ts']
                    logger.debug('lp: rewinding %r -> %r', old_ts, self.ts)
                elif code == 2:
                    logger.info('lp: key expired, renewing')
                    self.get_longpoll_server()
                elif code == 3:
                    logger.info('lp: we\'re lost, renewing key and ts')
                    self.get_longpoll_server()
                else:
                    logger.error('lp: something went wrong: %r', data)
                    raise LongpollException(data)
            else:
                self.ts = data['ts']
                for event in data['updates']:
                    logger.debug('lp: %r', event)
                    if self.group_id is None or self.raw:
                        yield event
                    else:
                        yield RDict.convert(event)
            if self.ts != self.master.session.get('lp', {}).get('ts'):
                self.update_session()

    def stop_polling(self):
        self._polling = False

