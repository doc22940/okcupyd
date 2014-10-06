import logging

import requests

from .errors import AuthenticationError
from . import settings
from . import util
from . import profile


log = logging.getLogger(__name__)


class Session(requests.Session):
    """A :ref:`requests.Session` with convenience methods for interacting with
    okcupid.com"""

    default_login_headers = {
        'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/37.0.2062.94 '
                       'Safari/537.36')
    }

    @classmethod
    def login(cls, username=None, password=None):
        """
        :param username: The username to log in with.
        :type username: str
        :param password: The password to log in with.
        :type password: str
        Get a session that has authenticated with okcupid.com.
        If no username or password is supplied, the
        """
        # settings.USERNAME and settings.PASSWORD should not be made
        # the defaults to their respective arguments because doing so
        # would prevent this function from picking up any changes made
        # to those values after import time.
        username = username or settings.USERNAME
        password = password or settings.PASSWORD
        session = cls()
        credentials = {
            'username': username,
            'password': password,
            'okc_api': 1
        }
        login_response = session.okc_post('login',
                                          data=credentials,
                                          headers=cls.default_login_headers,
                                          secure=True)
        log_in_name = login_response.json()['screenname']
        if log_in_name is None:
            raise AuthenticationError('Could not log in as {0}'.format(username))
        if log_in_name.lower() != username.lower():
            log.warning('Expected to log in as {0} but '
                        'got {1}'.format(username, log_in_name))
        log.debug(login_response.content.decode('utf8'))
        session.log_in_name = log_in_name
        session.headers.update(cls.default_login_headers)
        return session

    def get(self, *args, **kwargs):
        log.debug(kwargs)
        filter_keys = [key for key in kwargs.get('params', {}) if 'filter' in key]
        log.debug({k: kwargs.get('params', {})[k] for k in filter_keys})
        response = super(Session, self).get(*args, **kwargs)
        log.debug(response.content[:300])
        # log.debug(simplejson.dumps({'reponse': response.content[:300]}))
        response.raise_for_status()
        return response

    def post(self, *args, **kwargs):
        log.debug(kwargs)
        filter_keys = [key for key in kwargs.get('data', {}) if 'filter' in key]
        log.debug({k: kwargs.get('data', {})[k] for k in filter_keys})
        response = super(Session, self).post(*args, **kwargs)
        log.debug(response.content[:300])
        response.raise_for_status()
        return response

    def okc_get(self, path, secure=None, **kwargs):
        """Perform an HTTP GET to the www.okcupid.com at the provided path."""
        response = self.get(self.build_path(path, secure), **kwargs)
        return response

    def okc_post(self, path, secure=None, **kwargs):
        """Perform an HTTP POST to the www.okcupid.com at the provided path."""
        return self.post(self.build_path(path, secure), **kwargs)

    def build_path(self, path, secure=None):
        if secure is None:
            secure = ('secure_login' in self.cookies and
                      int(self.cookies['secure_login']) != 0)
        return u'{0}://{1}/{2}'.format('https' if secure else 'http',
                                       util.DOMAIN, path)

    def get_profile(self, username):
        """Get the profile associated with the supplied username
        :param username: The username of the profile to retrieve."""
        return profile.Profile(self, username)

    def get_current_user_profile(self):
        """Get the `okcupyd.profile.Profile`  associated with the supplied
        username.
        :param username: The username of the profile to retrieve.
        """
        return self.get_profile(self.log_in_name)
