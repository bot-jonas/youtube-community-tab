import json
from requests.utils import dict_from_cookiejar
from base64 import urlsafe_b64encode

from .helpers.utils import deep_get, CLIENT_VERSION
from .requests_handler import default_requests_handler
from .protobuf.keys.fixed_comment_params import fixed_comment_params


class Comment(object):
    POST_FORMAT_URL = "https://www.youtube.com/post/{}"
    FIXED_COMMENT_FORMAT_URL = "https://www.youtube.com/post/{}?lc={}"

    BROWSE_ENDPOINT = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
    UPDATE_COMMENT_ENDPOINT = "https://www.youtube.com/youtubei/v1/comment/update_comment?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"
    PERFORM_COMMENT_ACTION_ENDPOINT = (
        "https://www.youtube.com/youtubei/v1/comment/perform_comment_action?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"
    )

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
        requests_handler=default_requests_handler,
    ):
        self.post_id = post_id
        self.comment_id = comment_id
        self.channel_id = channel_id
        self.author = author
        self.content_text = content_text
        self.vote_count = vote_count
        self.replies = []

        self._requests_handler = requests_handler
        self._replies_continuation_token = replies_continuation_token

        self._click_tracking_params = click_tracking_params
        self._visitor_data = visitor_data
        self._session_index = session_index

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
        return self.content_text

    def load_replies(self):
        if self._replies_continuation_token:
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
                        "originalUrl": Comment.POST_FORMAT_URL.format(self.post_id),
                        "visitorData": self._visitor_data,
                    },
                },
                "continuation": self._replies_continuation_token,
                "clickTracking": {"clickTrackingParams": self._click_tracking_params},
            }

            resp = self._requests_handler.post(Comment.BROWSE_ENDPOINT, json=body, headers=headers)
            data = resp.json()

            mutations = data["frameworkUpdates"]["entityBatchUpdate"]["mutations"]
            payload_by_id = {}
            for mutation in mutations:
                payload = mutation["payload"]

                if "commentEntityPayload" not in payload:
                    continue

                payload = payload["commentEntityPayload"]
                comment_id = payload["properties"]["commentId"]

                payload_by_id[comment_id] = payload

            self._click_tracking_params = data["trackingParams"]
            continuation_items = deep_get(data, "onResponseReceivedEndpoints.0.appendContinuationItemsAction.continuationItems", default=[])

            self._append_replies_from_items(continuation_items, payload_by_id)

    def _append_replies_from_items(self, items, payload_by_id):
        there_is_no_continuation_token = True

        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentViewModel":
                reply_id = item[kind]["commentId"]
                self.replies.append(
                    Comment.from_data(
                        payload_by_id[reply_id],
                        self.post_id,
                        self.channel_id,
                        replies_continuation_token=None,
                        click_tracking_params=self._click_tracking_params,
                        visitor_data=self._visitor_data,
                        session_index=self._session_index,
                        requests_handler=self._requests_handler,
                    )
                )
            elif kind == "continuationItemRenderer":
                if "continuationEndpoint" in item[kind]:
                    self._replies_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                    there_is_no_continuation_token = False
                elif "button" in item[kind]:
                    self._replies_continuation_token = item[kind]["button"]["buttonRenderer"]["command"]["continuationCommand"]["token"]
                    there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self._replies_continuation_token = False

    @staticmethod
    def from_data(
        data,
        post_id,
        channel_id,
        replies_continuation_token,
        click_tracking_params,
        visitor_data,
        session_index,
        requests_handler=default_requests_handler,
    ):
        return Comment(
            post_id,
            data["properties"]["commentId"],
            channel_id=channel_id,
            content_text=deep_get(data, "properties.content.content"),
            author={
                "displayName": deep_get(data, "author.displayName"),
                "authorThumbnail": deep_get(data, "author.avatarThumbnailUrl"),
                # "authorEndpoint": deep_get(data, "authorEndpoint", "browseEndpoint"),
                # "authorIsChannelOwner": deep_get(data, "authorIsChannelOwner"),
                # "sponsorCommentBadge": deep_get(data, "sponsorCommentBadge"),
            },
            # vote_count=deep_get(data, "voteCount"),
            replies_continuation_token=replies_continuation_token,
            click_tracking_params=click_tracking_params,
            visitor_data=visitor_data,
            session_index=session_index,
            requests_handler=requests_handler,
        )

    @staticmethod
    def from_ids(comment_id, post_id, channel_id, requests_handler=default_requests_handler):
        fixed_comment_url = Comment.FIXED_COMMENT_FORMAT_URL.format(post_id, comment_id)

        c = fixed_comment_params(comment_id, post_id, channel_id)

        body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                    "originalUrl": fixed_comment_url,
                }
            },
            "continuation": c,
        }

        resp = requests_handler.post(Comment.BROWSE_ENDPOINT, json=body)
        data = resp.json()

        mutations = data["frameworkUpdates"]["entityBatchUpdate"]["mutations"]
        payload = None
        for mutation in mutations:
            payload = mutation["payload"]

            if "commentEntityPayload" not in payload:
                continue

            payload = payload["commentEntityPayload"]

            if comment_id == payload["properties"]["commentId"]:
                break

            payload = None

        if payload is not None:
            replies_continuation_endpoint_key = "onResponseReceivedEndpoints.1.reloadContinuationItemsCommand.continuationItems.0.commentThreadRenderer.replies.commentRepliesRenderer.contents.0.continuationItemRenderer.continuationEndpoint"  # noqa

            return Comment.from_data(
                payload,
                post_id,
                channel_id,
                replies_continuation_token=deep_get(data, f"{replies_continuation_endpoint_key}.continuationCommand.token"),
                click_tracking_params=deep_get(data, f"{replies_continuation_endpoint_key}.clickTrackingParams"),
                visitor_data=None,
                session_index=None,
                requests_handler=requests_handler,
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
        return Comment._update_comment(
            comment_text,
            comment_id=self.comment_id,
            post_id=self.post_id,
            channel_id=self.channel_id,
        )

    @staticmethod
    def _update_comment(
        comment_text,
        update_comment_params=None,
        comment_id=None,
        post_id=None,
        channel_id=None,
    ):
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
            b"\b\x06\x10\x07\x1a",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x00J\x15115587043600121621724P\x00\xa8\x01\x01\xb2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xba\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xf0\x01\x01",
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
            b"\b\x04\x10\x07\x1a",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x008",
            (not value).to_bytes(1, "big"),
            b"J\x15115587043600121621724P\x00\xa8\x01\x01\xb2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xba\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xf0\x01\x01",
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def set_dislike_comment(self, value=True):
        return Comment._set_dislike_comment(
            value,
            comment_id=self.comment_id,
            post_id=self.post_id,
            channel_id=self.channel_id,
        )

    @staticmethod
    def _set_dislike_comment(
        value,
        dislike_comment_params=None,
        comment_id=None,
        post_id=None,
        channel_id=None,
    ):
        if dislike_comment_params is None:
            dislike_comment_params = Comment.get_dislike_comment_params(value, comment_id, post_id, channel_id)

        return Comment.perform_action(dislike_comment_params)

    @staticmethod
    def get_like_comment_params(value, comment_id, post_id, channel_id):
        params = [
            b"\b\x05\x10\x07\x1a",
            len(comment_id).to_bytes(1, "big"),
            comment_id.encode(),
            b"0\x008",
            (not value).to_bytes(1, "big"),
            b"J\x15115587043600121621724P\x00\xa8\x01\x01\xb2\x01",
            len(post_id).to_bytes(1, "big"),
            post_id.encode(),
            b"\xba\x01",
            len(channel_id).to_bytes(1, "big"),
            channel_id.encode(),
            b"\xf0\x01\x01",
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def set_like_comment(self, value=True):
        return Comment._set_like_comment(
            value,
            comment_id=self.comment_id,
            post_id=self.post_id,
            channel_id=self.channel_id,
        )

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
