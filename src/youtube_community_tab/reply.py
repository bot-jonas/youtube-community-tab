import json

from .helpers.utils import safely_get_value_from_key


class Reply(object):
    def __init__(self, reply_id, content_text=None, author=None, num_likes=0):
        self.reply_id = reply_id
        self.content_text = content_text
        self.author = author
        self.num_likes = num_likes

    def as_json(self):
        return {
            "reply_id": self.reply_id,
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
    def from_data(data):
        reply = Reply(
            data["commentId"],
            content_text=safely_get_value_from_key(data, "contentText"),
            author=safely_get_value_from_key(data, "authorText", "simpleText"),
            num_likes=Reply.parse_vote_count(safely_get_value_from_key(data, "voteCount", "simpleText", default=0)),
        )

        reply.raw_data = data

        return reply
