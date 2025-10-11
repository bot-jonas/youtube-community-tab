from .comment import Comment
from .requests_handler import get_requests_handler
from .helpers.utils import deep_get
from .protobuf.keys.fixed_comment_params import fixed_comment_params
from .constants import (
    CLIENT_VERSION,
    BROWSE_ENDPOINT,
)


class CommentsIterator:
    def __init__(self, post):
        self.post = post

        self._first = True
        self._comments_continuation_token = fixed_comment_params(self.post.channel_id, self.post.post_id)
        self._comments = []

        self._click_tracking_params = None
        self._visitor_data = None
        self._session_index = "0"

    def __iter__(self):
        return self

    def __next__(self):
        if not self._comments:
            self._fetch_comments()

        if not self._comments:
            raise StopIteration

        return self._comments.pop(0)

    def _fetch_comments(self):
        if self._comments_continuation_token is False:
            return

        items, payload_by_id = self._get_comments_data()
        self._append_comments_from_items(items, payload_by_id)

    def _get_comments_data(self):
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
                    "originalUrl": self.post.post_url,
                    "visitorData": self._visitor_data,
                }
            },
            "continuation": self._comments_continuation_token,
            "clickTracking": {"clickTrackingParams": self._click_tracking_params},
        }

        resp = get_requests_handler().post(BROWSE_ENDPOINT, json=body, headers=headers)
        data = resp.json()

        # continuation_items are used to retrieve replies_continuation_token
        if self._first:
            key = "1.reloadContinuationItemsCommand"
            self._first = False
        else:
            key = "0.appendContinuationItemsAction"

        continuation_items = deep_get(data, f"onResponseReceivedEndpoints.{key}.continuationItems", default=[])

        # payloads are used to retrieve comment content
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

        return continuation_items, payload_by_id

    def _append_comments_from_items(self, items, payload_by_id):
        there_is_no_continuation_token = True
        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentThreadRenderer":
                comment_id = item[kind]["commentViewModel"]["commentViewModel"]["commentId"]
                payload = payload_by_id[comment_id]

                self._comments.append(
                    Comment.from_data(
                        payload,
                        self.post.post_id,
                        self.post.channel_id,
                    )
                )
            elif kind == "continuationItemRenderer":
                self._comments_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self._comments_continuation_token = False
