import json
from .helpers.utils import deep_get
from .requests_handler import default_requests_handler
from .protobuf.keys.fixed_comment_params import fixed_comment_params
from .protobuf.keys.perform_comment_action_params import perform_comment_action_params, CommentAction
from .protobuf.keys.update_comment_params import update_comment_params
from .helpers.logger import error
from .constants import (
    POST_URL_FORMAT,
    FIXED_COMMENT_URL_FORMAT,
    CLIENT_VERSION,
    BROWSE_ENDPOINT,
    UPDATE_COMMENT_ENDPOINT,
    PERFORM_COMMENT_ACTION_ENDPOINT,
)


class Comment(object):
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
                        "originalUrl": POST_URL_FORMAT.format(post_id=self.post_id),
                        "visitorData": self._visitor_data,
                    },
                },
                "continuation": self._replies_continuation_token,
                "clickTracking": {"clickTrackingParams": self._click_tracking_params},
            }

            resp = self._requests_handler.post(BROWSE_ENDPOINT, json=body, headers=headers)
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
        fixed_comment_url = FIXED_COMMENT_URL_FORMAT.format(post_id=post_id, comment_id=comment_id)

        c = fixed_comment_params(channel_id, post_id, comment_id)

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

        resp = requests_handler.post(BROWSE_ENDPOINT, json=body)
        data = resp.json()

        mutations = data["frameworkUpdates"]["entityBatchUpdate"]["mutations"]
        payload = None
        for mutation in mutations:
            payload = mutation["payload"]

            if "commentEntityPayload" not in payload:
                payload = None
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

    def update(self, comment_text):
        headers = {
            "x-origin": "https://www.youtube.com",
        }

        body = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": CLIENT_VERSION,
                },
            },
            "updateCommentParams": update_comment_params(self.comment_id, self.post_id, self.channel_id),
            "commentText": comment_text,
        }

        resp = self._requests_handler.post(UPDATE_COMMENT_ENDPOINT, json=body, headers=headers)
        data = resp.json()

        status = deep_get(data, "actions.0.updateCommentAction.actionResult.status")

        return status == "STATUS_SUCCEEDED"

    def add_like(self):
        return self._perform_action(CommentAction.ADD_LIKE)

    def remove_like(self):
        return self._perform_action(CommentAction.REMOVE_LIKE)

    def add_dislike(self):
        return self._perform_action(CommentAction.ADD_DISLIKE)

    def remove_dislike(self):
        return self._perform_action(CommentAction.REMOVE_DISLIKE)

    def add_heart(self):
        return self._perform_action(CommentAction.ADD_HEART)

    def remove_heart(self):
        return self._perform_action(CommentAction.REMOVE_HEART)

    def delete(self):
        return self._perform_action(CommentAction.DELETE)

    def _perform_action(self, action):
        action_params = perform_comment_action_params(
            self.comment_id,
            self.post_id,
            self.channel_id,
            action,
        )

        headers = {
            "x-origin": "https://www.youtube.com",
        }

        body = {
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

        resp = self._requests_handler.post(PERFORM_COMMENT_ACTION_ENDPOINT, json=body, headers=headers)

        if resp.status_code != 200:
            error("Could not perform the action")

        try:
            data = resp.json()
        except json.decoder.JSONDecodeError:
            error("Could not parse json")

        if action == CommentAction.DELETE:
            status = deep_get(data, "actions.0.removeCommentAction.actionResult.status")
        else:
            status = deep_get(data, "actionResults.0.status")

        return status == "STATUS_SUCCEEDED"
