import json
import re

from .helpers.utils import safely_get_value_from_key
from .requests_handler import requests_cache
from .comment import Comment


class Post(object):
    FORMAT_URLS = {
        "POST": "https://www.youtube.com/post/{}",
        # HARD_CODED: This key seems to be constant to everyone, IDK
        "BROWSE_ENDPOINT": "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    }

    REGEX = {
        "YT_INITIAL_DATA": "ytInitialData = ({(?:(?:.|\n)*)?});</script>",
    }

    def __init__(self, post_id, content_text=None, backstage_attachment=None):
        self.post_id = post_id
        self.content_text = content_text
        self.backstage_attachment = backstage_attachment

        self.first = True
        self.comments = []
        self.comments_continuation_token = None

    def as_json(self):
        return {
            "post_id": self.post_id,
            "content_text": self.content_text,
            "backstage_attachment": self.backstage_attachment,
        }

    @staticmethod
    def from_post_id(post_id, expire_after=0):
        post_url = Post.FORMAT_URLS["POST"].format(post_id)
        r = requests_cache.get(post_url, expire_after=expire_after)

        m = re.findall(Post.REGEX["YT_INITIAL_DATA"], r.text)
        data = json.loads(m[0])

        community_tab = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]
        community_tab_items = Post.get_items_from_community_tab(community_tab)

        post_data = community_tab_items[0]["backstagePostThreadRenderer"]["post"]["backstagePostRenderer"]

        return Post.from_data(post_data)

    def __str__(self):
        return json.dumps(self.as_json(), indent=4)

    def __repr__(self):
        return self.__str__()

    def get_thumbnails(self):
        # Returns a list of the thumbnails in different resolutions of
        # all images present in the post
        thumbnails = []

        if self.backstage_attachment is not None:
            renderer_key = list(self.backstage_attachment.keys())[0]

            if renderer_key == "videoRenderer":
                thumbnails = [self.backstage_attachment[renderer_key]["thumbnail"]["thumbnails"]]
            elif renderer_key == "backstageImageRenderer":
                thumbnails = [self.backstage_attachment[renderer_key]["image"]["thumbnails"]]
            elif renderer_key == "postMultiImageRenderer":
                thumbnails = [img["backstageImageRenderer"]["image"]["thumbnails"] for img in self.backstage_attachment[renderer_key]["images"]]
            elif renderer_key == "pollRenderer":
                print("[There is nothing implemented for polls]")
                thumbnails = []
            else:
                raise Exception("There is no implementation for renderer_key={renderer_key} yet")

        return thumbnails

    def get_first_continuation_token(self, data):
        self.comments_continuation_token = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"][
            "contents"
        ][1]["itemSectionRenderer"]["contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]

    def load_comments(self, expire_after=0):
        if self.comments_continuation_token is None:
            try:
                self.post_url = Post.FORMAT_URLS["POST"].format(self.post_id)
                r = requests_cache.get(self.post_url, expire_after=expire_after)

                m = re.findall(Post.REGEX["YT_INITIAL_DATA"], r.text)
                data = json.loads(m[0])

                self.get_first_continuation_token(data)
                self.load_comments(expire_after=expire_after)
            except Exception as e:
                print("[Some non-expected exception, probably caused by requests...]")
                raise e
        elif self.comments_continuation_token is not False:
            json_body = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20220121.01.00",
                        "originalUrl": self.post_url,
                    }
                },
                "continuation": self.comments_continuation_token,
            }

            r = requests_cache.post(
                Post.FORMAT_URLS["BROWSE_ENDPOINT"],
                json=json_body,
                expire_after=expire_after,
            )

            if self.first:
                if "continuationItems" not in r.json()["onResponseReceivedEndpoints"][1]["reloadContinuationItemsCommand"]:
                    # There are no comments
                    continuation_items = []
                else:
                    append = r.json()["onResponseReceivedEndpoints"][1]["reloadContinuationItemsCommand"]
                    continuation_items = safely_get_value_from_key(append, "continuationItems", default=[])
                    self.first = False
            else:
                append = r.json()["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
                continuation_items = safely_get_value_from_key(append, "continuationItems", default=[])

            self.append_comments_from_items(continuation_items)

    def append_comments_from_items(self, items):
        there_is_no_continuation_token = True
        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentThreadRenderer":
                self.comments.append(
                    Comment.from_data(
                        item[kind]["comment"]["commentRenderer"],
                        self.post_id,
                        safely_get_value_from_key(
                            item[kind],
                            "replies",
                            "commentRepliesRenderer",
                            "contents",
                            0,
                            "continuationItemRenderer",
                            "continuationEndpoint",
                            "continuationCommand",
                            "token",
                        ),
                    )
                )
            elif kind == "continuationItemRenderer":
                self.comments_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self.comments_continuation_token = False

    def get_text(self):
        runs = safely_get_value_from_key(self.content_text, "runs", default=[])

        if self.content_text is not None:
            return "\n".join([run["text"] for run in runs])
        return None

    @staticmethod
    def from_data(data):
        post = Post(
            data["postId"],
            content_text=safely_get_value_from_key(data, "contentText"),
            backstage_attachment=safely_get_value_from_key(data, "backstageAttachment"),
        )

        post.raw_data = data

        return post

    @staticmethod
    def get_items_from_community_tab(tab):
        try:
            return tab["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        except Exception as e:
            print("[Can't get the contents from the tab]")
            raise e
