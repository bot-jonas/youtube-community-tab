import json

from .helpers.utils import safely_get_value_from_key


class Reply(object):
    def __init__(self, reply_id, author=None, content_text=None, vote_count=None):
        self.reply_id = reply_id
        self.author = author
        self.content_text = content_text
        self.vote_count = vote_count

    def as_json(self):
        return {"reply_id": self.reply_id, "author": self.author, "content_text": self.content_text, "vote_count": self.vote_count}

    def __str__(self):
        return json.dumps(self.as_json(), indent=4)

    def __repr__(self):
        return self.__str__()

    def get_text(self):
        if self.content_text is not None:
            return "".join([run["text"] for run in self.content_text["runs"]])
        return None

    @staticmethod
    def from_data(data):
        reply = Reply(
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
        )

        reply.raw_data = data

        return reply
