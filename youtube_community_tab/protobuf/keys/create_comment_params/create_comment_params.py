from ...utils import message_to_key_urlsafe, message_from_json
from .create_comment_params_pb2 import CreateCommentParams


def create_comment_params(post_id, channel_id):
    return message_to_key_urlsafe(
        message_from_json(
            {
                "msg1": {
                    "int1": 0,
                },
                "int2": 1,
                "post_id": post_id,
                "channel_id": channel_id,
                "int3": 1,
            },
            CreateCommentParams,
        )
    )
