from .requests_handler import get_requests_handler
from .helpers.utils import deep_get
from .protobuf.keys.comment_replies_params import comment_replies_params
from .constants import (
    CLIENT_VERSION,
    BROWSE_ENDPOINT,
    POST_URL_FORMAT,
)


class RepliesIterator:
    def __init__(self, comment):
        self.comment = comment

        self._replies_continuation_token = comment_replies_params(self.comment.channel_id, self.comment.post_id, self.comment.comment_id)
        self._replies = []

        self._click_tracking_params = None
        self._visitor_data = None
        self._session_index = "0"

    def __iter__(self):
        return self

    def __next__(self):
        if not self._replies:
            self._fetch_replies()

        if not self._replies:
            raise StopIteration

        return self._replies.pop(0)

    def _fetch_replies(self):
        if self._replies_continuation_token is False:
            return

        items, payload_by_id = self._get_replies_data()
        self._append_replies_from_items(items, payload_by_id)

    def _get_replies_data(self):
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
                    "originalUrl": POST_URL_FORMAT.format(post_id=self.comment.post_id),
                    "visitorData": self._visitor_data,
                },
            },
            "continuation": self._replies_continuation_token,
            "clickTracking": {"clickTrackingParams": self._click_tracking_params},
        }

        resp = get_requests_handler().post(BROWSE_ENDPOINT, json=body, headers=headers)
        data = resp.json()

        mutations = deep_get(data, "frameworkUpdates.entityBatchUpdate.mutations")

        if mutations is None:
            self._replies_continuation_token = False
            return

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

        return continuation_items, payload_by_id

    def _append_replies_from_items(self, items, payload_by_id):
        # Avoid circular reference
        from .comment import Comment

        there_is_no_continuation_token = True

        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentViewModel":
                reply_id = item[kind]["commentId"]
                self._replies.append(
                    Comment.from_data(
                        payload_by_id[reply_id],
                        self.comment.post_id,
                        self.comment.channel_id,
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
