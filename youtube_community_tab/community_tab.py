import json
import re
from .helpers.utils import deep_get, CLIENT_VERSION
from .helpers.logger import error
from .requests_handler import default_requests_handler
from .post import Post


class CommunityTab:
    COMMUNITY_TAB_URL_FORMATS = {
        "CHANNEL_ID": "https://www.youtube.com/channel/{}/posts",  # UC6nSFpj9HTCZ5t-N3Rm3-HA
        "HANDLE": "https://www.youtube.com/{}/posts",  # @Vsauce
        "LEGACY_USERNAME": "https://www.youtube.com/c/{}/posts",  # vsauce1
    }

    BROWSE_ENDPOINT = "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"

    REGEX_YT_INITIAL_DATA = r"ytInitialData = ({(?:(?:.|\n)*)?});</script>"

    def __init__(self, channel, requests_handler=default_requests_handler):
        self.channel = channel
        self.channel_id = None
        self.posts = []

        self._requests_handler = requests_handler
        self._community_url = self._get_community_url()
        self._posts_continuation_token = None

        self._click_tracking_params = None
        self._visitor_data = None
        self._session_index = "0"

    def _get_community_url(self):
        if self.channel.startswith("UC"):
            return CommunityTab.COMMUNITY_TAB_URL_FORMATS["CHANNEL_ID"].format(self.channel)
        elif self.channel.startswith("@"):
            return CommunityTab.COMMUNITY_TAB_URL_FORMATS["HANDLE"].format(self.channel)
        else:
            return CommunityTab.COMMUNITY_TAB_URL_FORMATS["LEGACY_USERNAME"].format(self.channel)

    def load_posts(self):
        if self._posts_continuation_token is None:
            self._append_posts_from_items(self._get_initial_posts_data())
        elif self._posts_continuation_token is not False:
            self._append_posts_from_items(self._get_posts_data())

    def _get_initial_posts_data(self):
        resp = self._requests_handler.get(self._community_url)

        if resp.status_code != 200:
            error(f"Could not get data from the channel `{self.channel}` using the url `{self._community_url}`")

        matches = re.findall(CommunityTab.REGEX_YT_INITIAL_DATA, resp.text)

        if not matches:
            error("Could not find ytInitialData")

        try:
            ytInitialData = json.loads(matches[0])
        except json.decoder.JSONDecodeError:
            error("Could not parse json from ytInitialData")

        community_tab = self._get_community_tab(ytInitialData)

        # Update attributes
        self.channel_id = ytInitialData["metadata"]["channelMetadataRenderer"]["externalId"]
        self._update_session_attributes(community_tab, ytInitialData)

        return self._get_posts_data_from_community_tab(community_tab)

    def _get_posts_data(self):
        headers = {
            "X-Goog-AuthUser": self._session_index,
            "X-Origin": "https://www.youtube.com",
            "X-Youtube-Client-Name": "1",
            "X-Youtube-Client-Version": CLIENT_VERSION,
        }

        body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                    "originalUrl": self._community_url,
                    "visitorData": self._visitor_data,
                }
            },
            "continuation": self._posts_continuation_token,
            "clickTracking": {
                "clickTrackingParams": self._click_tracking_params,
            },
        }

        resp = self._requests_handler.post(CommunityTab.BROWSE_ENDPOINT, json=body, headers=headers)
        data = resp.json()

        posts_data = deep_get(data, "onResponseReceivedEndpoints.0.appendContinuationItemsAction.continuationItems", default=[])
        self._click_tracking_params = data["onResponseReceivedEndpoints"][0]["clickTrackingParams"]

        return posts_data

    def _append_posts_from_items(self, items):
        there_is_no_continuation_token = True

        for item in items:
            kind = list(item.keys())[0]

            if kind == "backstagePostThreadRenderer":
                self.posts.append(Post.from_data(item[kind]["post"], requests_handler=self._requests_handler))
            elif kind == "continuationItemRenderer":
                self._posts_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self._posts_continuation_token = False

    def _get_community_tab(self, ytInitialData):
        for tab in ytInitialData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]:
            url = deep_get(tab, "tabRenderer.endpoint.commandMetadata.webCommandMetadata.url", default="")

            if url.endswith("/posts"):
                return tab

        error("Could not find community tab in the ytInitialData")

    def _get_posts_data_from_community_tab(self, community_tab):
        try:
            return community_tab["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        except KeyError:
            error("Could not get the contents from the community tab")

    def _update_session_attributes(self, community_tab, ytInitialData):
        try:
            self._click_tracking_params = community_tab["tabRenderer"]["content"]["sectionListRenderer"]["trackingParams"]
        except KeyError:
            error("Could not get the click tracking params from the community tab")

        try:
            self._visitor_data = ytInitialData["responseContext"]["webResponseContextExtensionData"]["ytConfigData"]["visitorData"]
        except KeyError:
            error("Could not get the visitor data from the ytInitialData")

        self._session_index = str(deep_get(ytInitialData, "responseContext.webResponseContextExtensionData.ytConfigData.sessionIndex", default=""))
