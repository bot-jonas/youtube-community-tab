import json

from .requests_handler import requests_cache
from .helpers.utils import safely_get_value_from_key
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
        content_text=None,
        author=None,
        num_likes=0,
        replies_continuation_token=None,
    ):
        self.post_id = (post_id,)
        self.comment_id = comment_id
        self.content_text = content_text
        self.author = author
        self.num_likes = num_likes
        self.replies_continuation_token = replies_continuation_token
        self.replies = []

    def as_json(self):
        return {
            "comment_id": self.comment_id,
            "content_text": self.content_text,
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
        if self.replies_continuation_token:
            json_body = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20220121.01.00",
                        "originalUrl": Comment.FORMAT_URLS["POST"].format(self.post_id),
                    }
                },
                "continuation": self.replies_continuation_token,
            }

            r = requests_cache.post(
                Comment.FORMAT_URLS["BROWSE_ENDPOINT"],
                json=json_body,
                expire_after=expire_after,
            )

            append = r.json()["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
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

        if there_is_no_continuation_token:
            self.replies_continuation_token = False

    @staticmethod
    def parse_vote_count(vote_count):
        try:
            return int(vote_count)
        except ValueError:
            factors = {
                "K": 1e3,
                "M": 1e6,
            }

            return int(float(vote_count[:-1]) * factors[vote_count[-1]])

    @staticmethod
    def from_data(data, post_id, replies_continuation_token):
        comment = Comment(
            post_id,
            data["commentId"],
            content_text=safely_get_value_from_key(data, "contentText"),
            author=safely_get_value_from_key(data, "authorText", "simpleText"),
            num_likes=Comment.parse_vote_count(safely_get_value_from_key(data, "voteCount", "simpleText", default=0)),
            replies_continuation_token=replies_continuation_token,
        )

        comment.raw_data = data

        return comment
