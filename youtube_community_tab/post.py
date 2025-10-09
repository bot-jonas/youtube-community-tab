import json
import re
from requests.utils import dict_from_cookiejar
from base64 import urlsafe_b64encode

from .helpers.clean_items import clean_content_text, clean_backstage_attachment
from .helpers.utils import deep_get, CLIENT_VERSION, search_key
from .helpers.logger import error
from .requests_handler import default_requests_handler
from .comment import Comment


class Post(object):
    POST_URL_FORMAT = "https://www.youtube.com/post/{}"
    BROWSE_ENDPOINT = "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    CREATE_COMMENT_ENDPOINT = "https://www.youtube.com/youtubei/v1/comment/create_comment?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"
    REGEX_YT_INITIAL_DATA = r"ytInitialData = ({(?:(?:.|\n)*)?});</script>"

    def __init__(
        self,
        post_id,
        channel_id=None,
        author=None,
        content_text=None,
        backstage_attachment=None,
        vote_count=None,
        sponsor_only_badge=None,
        published_time_text=None,
        original_post=None,
        requests_handler=default_requests_handler,
    ):
        self.post_id = post_id
        self.channel_id = channel_id
        self.author = author
        self.content_text = content_text
        self.backstage_attachment = backstage_attachment
        self.vote_count = vote_count
        self.sponsor_only_badge = sponsor_only_badge
        self.published_time_text = published_time_text
        self.original_post = original_post
        self.comments = []

        self._requests_handler = requests_handler
        self._post_url = Post.POST_URL_FORMAT.format(self.post_id)
        self._first = True
        self._comments_continuation_token = None

        self._click_tracking_params = None
        self._visitor_data = None
        self._session_index = "0"

    def as_json(self):
        return {
            "post_id": self.post_id,
            "channel_id": self.channel_id,
            "author": self.author,
            "content_text": self.content_text,
            "backstage_attachment": self.backstage_attachment,
            "vote_count": self.vote_count,
            "sponsor_only_badge": self.sponsor_only_badge,
            "original_post": self.original_post,
        }

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

    def load_comments(self):
        if self._comments_continuation_token is None:
            resp = self._requests_handler.get(self._post_url)

            if resp.status_code != 200:
                error(f"Could not get data from the post_id `{self.post_id}` using the url `{self._post_url}`")

            matches = re.findall(Post.REGEX_YT_INITIAL_DATA, resp.text)

            if not matches:
                error("Could not find ytInitialData")

            try:
                ytInitialData = json.loads(matches[0])
            except json.decoder.JSONDecodeError:
                error("Could not parse json from ytInitialData")

            self._get_first_continuation_token(ytInitialData)

            self._update_session_attributes(ytInitialData)

            self.load_comments()
        elif self._comments_continuation_token is not False:
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
                        "originalUrl": Post.POST_URL_FORMAT.format(self.post_id),
                        "visitorData": self._visitor_data,
                    }
                },
                "continuation": self._comments_continuation_token,
                "clickTracking": {"clickTrackingParams": self._click_tracking_params},
            }

            resp = self._requests_handler.post(Post.BROWSE_ENDPOINT, json=body, headers=headers)
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

            if self._first:
                if "continuationItems" not in data["onResponseReceivedEndpoints"][1]["reloadContinuationItemsCommand"]:
                    # There are no comments
                    continuation_items = []
                else:
                    append = data["onResponseReceivedEndpoints"][1]["reloadContinuationItemsCommand"]
                    continuation_items = deep_get(append, "continuationItems", default=[])
                    self._first = False
            else:
                append = data["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
                continuation_items = deep_get(append, "continuationItems", default=[])

            self._click_tracking_params = data["trackingParams"]

            self._append_comments_from_items(continuation_items, payload_by_id)

    def _get_first_continuation_token(self, ytInitialData):
        self._comments_continuation_token = ytInitialData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"][
            "sectionListRenderer"
        ]["contents"][1]["itemSectionRenderer"]["contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]

    def _update_session_attributes(self, ytInitialData):
        self._click_tracking_params = ytInitialData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"][
            "contents"
        ][1]["itemSectionRenderer"]["contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["clickTrackingParams"]

        self._visitor_data = ytInitialData["responseContext"]["webResponseContextExtensionData"]["ytConfigData"]["visitorData"]
        self._session_index = str(deep_get(ytInitialData, "responseContext.webResponseContextExtensionData.ytConfigData.sessionIndex"))

    def _append_comments_from_items(self, items, payload_by_id):
        there_is_no_continuation_token = True
        for item in items:
            kind = list(item.keys())[0]

            if kind == "commentThreadRenderer":
                replies_continuation_endpoint_key = "replies.commentRepliesRenderer.contents.0.continuationItemRenderer.continuationEndpoint"

                comment_id = item[kind]["commentViewModel"]["commentViewModel"]["commentId"]
                payload = payload_by_id[comment_id]

                self.comments.append(
                    Comment.from_data(
                        payload,
                        self.post_id,
                        self.channel_id,
                        deep_get(item[kind], f"{replies_continuation_endpoint_key}.continuationCommand.token"),
                        deep_get(item[kind], f"{replies_continuation_endpoint_key}.clickTrackingParams"),
                        self._visitor_data,
                        self._session_index,
                        requests_handler=self._requests_handler,
                    )
                )
            elif kind == "continuationItemRenderer":
                self._comments_continuation_token = item[kind]["continuationEndpoint"]["continuationCommand"]["token"]
                there_is_no_continuation_token = False

        if there_is_no_continuation_token:
            self._comments_continuation_token = False

    def get_text(self):
        runs = deep_get(self.content_text, "runs", default=[])

        if self.content_text is not None:
            return "\n".join([run["text"] for run in runs])
        return None

    def get_published_string(self):
        return self.published_time_text

    def get_create_comment_params(self):
        if self.channel_id is None or self.post_id is None:
            return None

        params = [
            b"*\x02\b\x00P\x01\xa2\x01",
            len(self.post_id).to_bytes(1, "big"),
            self.post_id.encode(),
            b"\xaa\x01",
            len(self.channel_id).to_bytes(1, "big"),
            self.channel_id.encode(),
        ]

        params = urlsafe_b64encode(b"".join(params)).decode().replace("=", "%3D")

        return params

    def create_comment(self, comment_text):
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
            "createCommentParams": self.get_create_comment_params(),
            "commentText": comment_text,
        }

        r = requests_cache.post(
            Post.FORMAT_URLS["CREATE_COMMENT_ENDPOINT"],
            json=json_body,
            headers=headers,
        )

        try:
            data = r.json()
            comment_id = search_key("comment", data)[0][1]["commentRenderer"]["commentId"]

            return Comment.from_ids(comment_id, self.post_id, self.channel_id)
        except Exception as e:
            raise e

    @staticmethod
    def from_post_id(post_id, requests_handler=default_requests_handler):
        post_url = Post.POST_URL_FORMAT.format(post_id)
        resp = requests_handler.get(post_url)

        if resp.status_code != 200:
            error(f"Could not get data from the post_id `{post_id}` using the url `{post_url}`")

        matches = re.findall(Post.REGEX_YT_INITIAL_DATA, resp.text)

        if not matches:
            error("Could not find ytInitialData")

        try:
            ytInitialData = json.loads(matches[0])
        except json.decoder.JSONDecodeError:
            error("Could not parse json from ytInitialData")

        community_tab = ytInitialData["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]
        community_tab_items = Post.get_items_from_community_tab(community_tab)

        post_data = community_tab_items[0]["backstagePostThreadRenderer"]["post"]

        post = Post.from_data(post_data)
        post._get_first_continuation_token(ytInitialData)
        post._update_session_attributes(ytInitialData)

        return post

    @staticmethod
    def from_data(data, requests_handler=default_requests_handler) -> "Post":
        post_kind = list(data.keys())[0]

        if post_kind == "backstagePostRenderer":
            return Post._from_backstage_post_renderer_data(data["backstagePostRenderer"], requests_handler)
        elif post_kind == "sharedPostRenderer":
            return Post._from_shared_post_renderer_data(data["sharedPostRenderer"], requests_handler)
        else:
            raise NotImplementedError(f"post_kind={post_kind} is not implemented")

    @staticmethod
    def _from_backstage_post_renderer_data(data, requests_handler=default_requests_handler):
        return Post(
            data["postId"],
            channel_id=deep_get(data, "authorEndpoint.browseEndpoint.browseId"),
            author={
                "authorText": deep_get(data, "authorText"),
                "authorThumbnail": deep_get(data, "authorThumbnail"),
                "authorEndpoint": deep_get(data, "authorEndpoint"),
            },
            content_text=clean_content_text(deep_get(data, "contentText")),
            backstage_attachment=clean_backstage_attachment(deep_get(data, "backstageAttachment")),
            vote_count=deep_get(data, "voteCount"),
            sponsor_only_badge=deep_get(data, "sponsorsOnlyBadge"),
            published_time_text=deep_get(data, "publishedTimeText.runs.0.text"),
            requests_handler=requests_handler,
        )

    @staticmethod
    def _from_shared_post_renderer_data(data, requests_handler=default_requests_handler):
        data["authorText"] = data["displayName"]
        data["authorEndpoint"] = data["endpoint"]
        data["contentText"] = data["content"]

        return Post(
            data["postId"],
            channel_id=deep_get(data, "authorEndpoint.browseEndpoint.browseId"),
            author={
                "authorText": deep_get(data, "authorText"),
                "authorThumbnail": deep_get(data, "authorThumbnail"),
                "authorEndpoint": deep_get(data, "authorEndpoint"),
            },
            content_text=clean_content_text(deep_get(data, "contentText")),
            backstage_attachment=clean_backstage_attachment(deep_get(data, "backstageAttachment")),
            vote_count=deep_get(data, "voteCount"),
            sponsor_only_badge=deep_get(data, "sponsorsOnlyBadge"),
            published_time_text=deep_get(data, "publishedTimeText.runs.0.text"),
            original_post=Post.from_data(data["originalPost"]),
            requests_handler=requests_handler,
        )

    @staticmethod
    def get_items_from_community_tab(tab):
        try:
            return tab["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        except Exception as e:
            print("[Can't get the contents from the tab]")
            raise e
