from .posts_iterator import PostsIterator
from .constants import (
    COMMUNITY_TAB_CHANNEL_ID_URL_FORMAT,
    COMMUNITY_TAB_HANDLE_URL_FORMAT,
    COMMUNITY_TAB_LEGACY_USERNAME_URL_FORMAT,
)


class Channel:
    def __init__(self, identifier):
        self.identifier = identifier
        self.community_url = self._get_community_url()

    def _get_community_url(self):
        if self.identifier.startswith("UC"):
            return COMMUNITY_TAB_CHANNEL_ID_URL_FORMAT.format(channel_id=self.identifier)
        elif self.identifier.startswith("@"):
            return COMMUNITY_TAB_HANDLE_URL_FORMAT.format(handle=self.identifier)
        else:
            return COMMUNITY_TAB_LEGACY_USERNAME_URL_FORMAT.format(legacy_username=self.identifier)

    def posts(self):
        return PostsIterator(self)
