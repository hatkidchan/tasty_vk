# -*- coding: utf-8 -*-
import os
import pickle
import logging


SESSIONS_HOME = os.curdir
logger = logging.getLogger('tasty_vk')


class RDict(dict):
    @classmethod
    def convert(cls, value):
        """
        Recursively converts any type to RDict, if possible
        """
        if isinstance(value, dict):
            return cls(**{
                k: cls.convert(v)
                for k, v
                in value.items()
            })
        elif isinstance(value, (list, tuple)):
            return [
                cls.convert(v)
                for v
                in value
            ]
        else:
            return value

    @classmethod
    def revert(cls, value):
        """
        Recursively reverts conversion to RDict, if possible
        """
        if isinstance(value, cls):
            return {
                k: cls.revert(v)
                for k, v
                in value.items()
            }
        elif isinstance(value, (list, tuple)):
            return [
                cls.revert(v)
                for v
                in value
            ]
        else:
            return value

    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        for k, v in kwargs.items():
            if k in dir(dict):
                k = '_' + k
            setattr(self, k, self.convert(v))


class ApiException(ValueError):
    pass


class LongpollException(ApiException):
    pass


class ParseError(ValueError):
    pass


class VKSession(dict):
    def __init__(self, session_name):
        super().__init__({
            '_': {
                'name': session_name,
                'access_token': None
            }
        })
        self.name = session_name

    @property
    def path(self):
        return os.path.abspath(os.path.join(SESSIONS_HOME, self.name + '.vks'))

    def save(self):
        if self.name == ':memory:':
            return False
        with open(self.path, 'wb') as fd:
            pickle.dump(dict(self), fd)
        logger.debug('session saved')

    def load(self):
        if self.name == ':memory:':
            return False
        try:
            with open(self.path, 'rb') as fd:
                self.update(pickle.load(fd))
        except FileNotFoundError:
            logger.info('session %r not exists, creating', self.path)
        except Exception as e:
            logger.error('%r occurred while loading. session is broken.', e)
            raise e

