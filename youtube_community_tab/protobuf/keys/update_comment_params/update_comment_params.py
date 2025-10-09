from ...utils import message_to_key_urlsafe, message_from_json
from .update_comment_params_pb2 import UpdateCommentParams


def update_comment_params(comment_id, post_id, channel_id):
    return message_to_key_urlsafe(
        message_from_json(
            {
                "comment_id": comment_id,
                "msg1": {
                    "int1": 0,
                },
                "int2": 1,
                "post_id": post_id,
                "channel_id": channel_id,
                "str1": "",
            },
            UpdateCommentParams,
        )
    )
