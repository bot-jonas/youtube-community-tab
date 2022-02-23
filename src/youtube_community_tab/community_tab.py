import re
import json

from .requests_handler import requests_cache
from .helpers.utils import safely_get_value_from_key
from .post import Post


class CommunityTab(object):
    FORMAT_URLS = {
        "COMMUNITY_TAB": "https://www.youtube.com/{}/{}/community",
        # HARD_CODED: This key seems to be constant to everyone, IDK
        "BROWSE_ENDPOINT": "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    }

    REGEX = {
        "YT_INITIAL_DATA": "ytInitialData = ({(?:(?:.|\n)*)?});</script>",
    }

    def __init__(self, channel_name):
        self.channel_name = channel_name

        self.posts_continuation_token = None
        self.posts = []
        self.community_url = None

    def load_posts(self, expire_after=0):
        if self.posts_continuation_token is None:
            try:
                # Get posts from community tab enpoint
                self.community_url = CommunityTab.FORMAT_URLS["COMMUNITY_TAB"].format("c", self.channel_name)
                r = requests_cache.get(self.community_url, expire_after=expire_after)
                if r.status_code != 200:
                    self.community_url = CommunityTab.FORMAT_URLS["COMMUNITY_TAB"].format("channel", self.channel_name)
                    r = requests_cache.get(self.community_url, expire_after=expire_after)

                if r.status_code != 200:
                    import sys

                    print(f"[Can't get data from the channel_name: {self.channel_name}]")
                    sys.exit()

                m = re.findall(CommunityTab.REGEX["YT_INITIAL_DATA"], r.text)
                data = json.loads(m[0])
            except IndexError as e:
                print("[Can't find yt_initial_data using the regex]")
                raise e
            except json.decoder.JSONDecodeError as e:
                print("[Can't parse yt_initial_data from the regex]")
                raise e
            except Exception as e:
                print("[Some non-expected exception, probably caused by requests...]")
                raise e

            tabs = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
            community_tab_items = CommunityTab.get_items_from_community_tab(CommunityTab.get_community_tab(tabs))

            self.append_posts_from_items(community_tab_items)
        elif self.posts_continuation_token is not False:
            json_body = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20220121.01.00",
                        "originalUrl": self.community_url,
                    }
                },
                "continuation": self.posts_continuation_token,
            }

            r = requests_cache.post(
                CommunityTab.FORMAT_URLS["BROWSE_ENDPOINT"],
                json=json_body,
                expire_after=expire_after,
            )

            append = r.json()["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
            self.append_posts_from_items(safely_get_value_from_key(append, "continuationItems", default=[]))

    def append_posts_from_items(self, items):
        there_is_no_continuation_token = True
        for item in items:
            kind = list(item.keys())[0]

            if kind == "backstagePostThreadRenderer":
                self.posts.append(Post.from_data(item[kind]["post"]["backstagePostRenderer"]))
            elif kind == "continuationItemRenderer":
                self.posts_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self.posts_continuation_token = False

    @staticmethod
    def get_community_tab(tabs):
        COMMUNITY_TAB_INDEX = 3

        if len(tabs) >= COMMUNITY_TAB_INDEX + 1:
            return tabs[COMMUNITY_TAB_INDEX]
        else:
            raise Exception(f"[The community tab is expected to have index equal to {COMMUNITY_TAB_INDEX}, but len(tabs) = {len(tabs)}]")

    @staticmethod
    def get_items_from_community_tab(tab):
        try:
            return tab["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        except Exception as e:
            print("[Can't get the contents from the tab]")
            raise e
