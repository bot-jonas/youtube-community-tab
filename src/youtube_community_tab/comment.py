import json
from requests.utils import dict_from_cookiejar
from base64 import urlsafe_b64encode

from .requests_handler import requests_cache
from .helpers.utils import safely_get_value_from_key, get_auth_header, CLIENT_VERSION
from .reply import Reply


class Comment(object):
    FORMAT_URLS = {
        "POST": "https://www.youtube.com/post/{}",
        # HARD_CODED: This key seems to be constant to everyone, IDK
        "BROWSE_ENDPOINT": "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
        "UPDATE_COMMENT_ENDPOINT": "https://www.youtube.com/youtubei/v1/comment/update_comment?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false",
        "PERFORM_COMMENT_ACTION_ENDPOINT": "https://www.youtube.com/youtubei/v1/comment/perform_comment_action?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false",
        "FIXED_COMMENT": "https://www.youtube.com/channel/{}/community?lc={}&lb={}",
    }

    def __init__(
        self,
        post_id,
        comment_id,
        channel_id=None,
        author=None,
        content_text=None,
        vote_count=None,
        replies_continuation_token=None,
        click_tracking_params=None,
        visitor_data=None,
        session_index="0",
    ):
        self.post_id = post_id
        self.comment_id = comment_id
        self.channel_id = channel_id
        self.author = author
        self.content_text = content_text
        self.vote_count = vote_count
        self.replies_continuation_token = replies_continuation_token
        self.click_tracking_params = click_tracking_params
        self.visitor_data = visitor_data
        self.session_index = session_index
        self.replies = []

    def as_json(self):
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "channel_id": self.channel_id,
            "author": self.author,
            "content_text": self.content_text,
            "vote_count": self.vote_count,
        }

    def __str__(self):
        return json.dumps(self.as_json(), indent=4)

    def __repr__(self):
        return self.__str__()

    def get_text(self):
        if self.content_text is not None:
            return "".join([run["text"] for run in self.content_text["runs"]])
        return None

    def load_replies(self, expire_after=0):
        headers = {
            "x-origin": "https://www.youtube.com",
            "Referer": Comment.FORMAT_URLS["POST"].format(self.post_id),
        }

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
            append = safely_get_value_from_key(data, "onResponseReceivedEndpoints", 0, "appendContinuationItemsAction", default=[])
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
    def from_data(data, post_id, channel_id, replies_continuation_token, click_tracking_params, visitor_data, session_index):
        comment = Comment(
            post_id,
            data["commentId"],
            channel_id=channel_id,
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

    @staticmethod
    def get_fixed_comment_params(comment_id, post_id, channel_id):
        part1 = [
            b"\x12\tcommunity\xB8\x01\x00\xCA\x01",
            (32 + len(post_id)).to_bytes(1, "big"),
            b"\x82\x01",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"\xB2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xEA\x02\x04\x10\x01\x18\x01\xAA\x03",
            (84 + len(post_id)).to_bytes(1, "big"),
            b"\x22",
            (64 + len(post_id)).to_bytes(1, "big"),
            b"0\x00\x82\x01",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"\xD8\x01\x01\xEA\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xF2\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"B\x10comments-section",
        ]

        part1 = urlsafe_b64encode(b"".join(part1)).replace(b"=", b"%3D")

        params = [
            b"\xe2\xa9\x85\xb2\x02",
            (83 + 3 * len(post_id)).to_bytes(1, "big"),
            b"\x02\x12",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\x1A",
            (54 + 3 * len(post_id)).to_bytes(1, "big"),
            b"\x02",
            part1,
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    @staticmethod
    def from_ids(comment_id, post_id, channel_id, expire_after=0):
        fixed_comment_url = Comment.FORMAT_URLS["FIXED_COMMENT"].format(channel_id, comment_id, post_id)
        headers = {
            "x-origin": "https://www.youtube.com",
            "Referer": fixed_comment_url,
        }

        # Add authorization header
        current_cookies = dict_from_cookiejar(requests_cache.cookies)
        if "SAPISID" in current_cookies:
            headers["Authorization"] = get_auth_header(current_cookies["SAPISID"])

        c = Comment.get_fixed_comment_params(comment_id, post_id, channel_id)

        json_body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                    "originalUrl": fixed_comment_url,
                }
            },
            "continuation": c,
        }

        r = requests_cache.post(Comment.FORMAT_URLS["BROWSE_ENDPOINT"], json=json_body, expire_after=expire_after, headers=headers)

        comment_data = safely_get_value_from_key(
            r.json(), "onResponseReceivedEndpoints", 1, "reloadContinuationItemsCommand", "continuationItems", 0, "commentThreadRenderer"
        )

        if comment_data is not None:
            return Comment.from_data(
                comment_data["comment"]["commentRenderer"],
                post_id,
                channel_id,
                safely_get_value_from_key(
                    comment_data,
                    "replies",
                    "commentRepliesRenderer",
                    "contents",
                    0,
                    "continuationItemRenderer",
                    "continuationEndpoint",
                    "continuationCommand",
                    "token",
                ),
                safely_get_value_from_key(
                    comment_data,
                    "replies",
                    "commentRepliesRenderer",
                    "contents",
                    0,
                    "continuationItemRenderer",
                    "continuationEndpoint",
                    "clickTrackingParams",
                ),
                None,
                None,
            )

    @staticmethod
    def get_update_comment_params(comment_id, post_id, channel_id):
        params = [
            b"\n",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"*\x02\b\x00@\x01R",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"Z",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def update_comment(self, comment_text):
        return Comment._update_comment(comment_text, comment_id=self.comment_id, post_id=self.post_id, channel_id=self.channel_id)

    @staticmethod
    def _update_comment(comment_text, update_comment_params=None, comment_id=None, post_id=None, channel_id=None):
        if update_comment_params is None:
            update_comment_params = Comment.get_update_comment_params(comment_id, post_id, channel_id)

        headers = {
            "x-origin": "https://www.youtube.com",
        }

        current_cookies = dict_from_cookiejar(requests_cache.cookies)
        if "SAPISID" in current_cookies:
            headers["Authorization"] = get_auth_header(current_cookies["SAPISID"])

        json_body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                },
            },
            "updateCommentParams": update_comment_params,
            "commentText": comment_text,
        }

        r = requests_cache.post(
            Comment.FORMAT_URLS["UPDATE_COMMENT_ENDPOINT"],
            json=json_body,
            headers=headers,
        )

        return r.json()

    @staticmethod
    def get_delete_comment_params(comment_id, post_id, channel_id):
        params = [
            b"\b\x06\x10\x07\x1A",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x00J\x15115587043600121621724P\x00\xA8\x01\x01\xB2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xBA\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xF0\x01\x01",
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def delete_comment(self):
        return Comment._delete_comment(comment_id=self.comment_id, post_id=self.post_id, channel_id=self.channel_id)

    @staticmethod
    def _delete_comment(delete_comment_params=None, comment_id=None, post_id=None, channel_id=None):
        if delete_comment_params is None:
            delete_comment_params = Comment.get_delete_comment_params(comment_id, post_id, channel_id)

        return Comment.perform_action(delete_comment_params)

    @staticmethod
    def get_dislike_comment_params(value, comment_id, post_id, channel_id):
        params = [
            b"\b\x04\x10\x07\x1A",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x008",
            (not value).to_bytes(1, "big"),
            b"J\x15115587043600121621724P\x00\xA8\x01\x01\xB2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xBA\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xF0\x01\x01",
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def set_dislike_comment(self, value=True):
        return Comment._set_dislike_comment(value, comment_id=self.comment_id, post_id=self.post_id, channel_id=self.channel_id)

    @staticmethod
    def _set_dislike_comment(value, dislike_comment_params=None, comment_id=None, post_id=None, channel_id=None):
        if dislike_comment_params is None:
            dislike_comment_params = Comment.get_dislike_comment_params(value, comment_id, post_id, channel_id)

        return Comment.perform_action(dislike_comment_params)

    @staticmethod
    def get_like_comment_params(value, comment_id, post_id, channel_id):
        params = [
            b"\b\x05\x10\x07\x1A",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x008",
            (not value).to_bytes(1, "big"),
            b"J\x15115587043600121621724P\x00\xA8\x01\x01\xB2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xBA\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xF0\x01\x01",
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def set_like_comment(self, value=True):
        return Comment._set_like_comment(value, comment_id=self.comment_id, post_id=self.post_id, channel_id=self.channel_id)

    @staticmethod
    def _set_like_comment(value, like_comment_params=None, comment_id=None, post_id=None, channel_id=None):
        if like_comment_params is None:
            like_comment_params = Comment.get_like_comment_params(value, comment_id, post_id, channel_id)

        return Comment.perform_action(like_comment_params)

    @staticmethod
    def perform_action(action_params):
        headers = {
            "x-origin": "https://www.youtube.com",
        }

        current_cookies = dict_from_cookiejar(requests_cache.cookies)
        if "SAPISID" in current_cookies:
            headers["Authorization"] = get_auth_header(current_cookies["SAPISID"])

        json_body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                },
            },
            "actions": [
                action_params,
            ],
        }

        r = requests_cache.post(
            Comment.FORMAT_URLS["PERFORM_COMMENT_ACTION_ENDPOINT"],
            json=json_body,
            headers=headers,
        )

        return r.json()
