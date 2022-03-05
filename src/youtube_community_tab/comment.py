import json
from requests.utils import dict_from_cookiejar

from .requests_handler import requests_cache
from .helpers.utils import safely_get_value_from_key, get_auth_header, CLIENT_VERSION
from .reply import Reply


class Comment(object):
    FORMAT_URLS = {
        "POST": "https://www.youtube.com/post/{}",
        # HARD_CODED: This key seems to be constant to everyone, IDK
        "BROWSE_ENDPOINT": "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
    }

    def __init__(
        self,
        post_id,
        comment_id,
        author=None,
        content_text=None,
        vote_count=None,
        replies_continuation_token=None,
        click_tracking_params=None,
        visitor_data=None,
        session_index="0",
    ):
        self.post_id = (post_id,)
        self.comment_id = comment_id
        self.author = author
        self.content_text = content_text
        self.vote_count = vote_count
        self.replies_continuation_token = replies_continuation_token
        self.click_tracking_params = click_tracking_params
        self.visitor_data = visitor_data
        self.session_index = session_index
        self.replies = []

    def as_json(self):
        return {"comment_id": self.comment_id, "author": self.author, "content_text": self.content_text, "vote_count": self.vote_count}

    def __str__(self):
        return json.dumps(self.as_json(), indent=4)

    def __repr__(self):
        return self.__str__()

    def get_text(self):
        if self.content_text is not None:
            return "".join([run["text"] for run in self.content_text["runs"]])
        return None

    def load_replies(self, expire_after=0):
        headers = {"Referer": Comment.FORMAT_URLS["POST"].format(self.post_id)}

        # Add authorization header
        current_cookies = dict_from_cookiejar(requests_cache.cookies)
        if "SAPISID" in current_cookies:
            headers["Authorization"] = get_auth_header(current_cookies["SAPISID"])

        if self.replies_continuation_token:
            headers.update(
                {
                    "X-Goog-AuthUser": self.session_index,
                    "X-Origin": "https://www.youtube.com",
                    "X-Youtube-Client-Name": "1",
                    "X-Youtube-Client-Version": CLIENT_VERSION,
                }
            )

            json_body = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": CLIENT_VERSION,
                        "originalUrl": Comment.FORMAT_URLS["POST"].format(self.post_id),
                        "visitorData": self.visitor_data,
                    }
                },
                "continuation": self.replies_continuation_token,
                "clickTracking": {"clickTrackingParams": self.click_tracking_params},
            }

            r = requests_cache.post(Comment.FORMAT_URLS["BROWSE_ENDPOINT"], json=json_body, expire_after=expire_after, headers=headers)

            data = r.json()
            append = data["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
            self.click_tracking_params = data["trackingParams"]
            continuation_items = safely_get_value_from_key(append, "continuationItems", default=[])

            self.append_replies_from_items(continuation_items)

    def append_replies_from_items(self, items):
        there_is_no_continuation_token = True
        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentRenderer":
                self.replies.append(Reply.from_data(item[kind]))
            elif kind == "continuationItemRenderer":
                if "continuationEndpoint" in item[kind]:
                    self.replies_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                    there_is_no_continuation_token = False
                elif "button" in item[kind]:
                    self.replies_continuation_token = item[kind]["button"]["buttonRenderer"]["command"]["continuationCommand"]["token"]
                    there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self.replies_continuation_token = False

    @staticmethod
    def from_data(data, post_id, replies_continuation_token, click_tracking_params, visitor_data, session_index):
        comment = Comment(
            post_id,
            data["commentId"],
            content_text=safely_get_value_from_key(data, "contentText"),
            author={
                "authorText": safely_get_value_from_key(data, "authorText"),
                "authorThumbnail": safely_get_value_from_key(data, "authorThumbnail"),
                "authorEndpoint": safely_get_value_from_key(data, "authorEndpoint", "browseEndpoint"),
                "authorIsChannelOwner": safely_get_value_from_key(data, "authorIsChannelOwner"),
                "sponsorCommentBadge": safely_get_value_from_key(data, "sponsorCommentBadge"),
            },
            vote_count=safely_get_value_from_key(data, "voteCount"),
            replies_continuation_token=replies_continuation_token,
            click_tracking_params=click_tracking_params,
            visitor_data=visitor_data,
            session_index=session_index,
        )

        comment.raw_data = data

        return comment
