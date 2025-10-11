from ...utils import message_to_key_urlsafe, message_from_json
from .comment_replies_params_pb2 import CommentRepliesParams, InnerCommentRepliesParams


def comment_replies_params(channel_id, post_id, comment_id):
    data = {
        "str2": "posts",
        "msg2": {
            "post_id": post_id,
        },
        "msg3": {
            "int2": 1,
            "int3": 1,
        },
        "msg4": {
            "msg5": {
                "comment_id": comment_id,
                "msg6": {
                    "int1": 0,
                },
                "channel_id": channel_id,
                "int8": 1,
                "int9": 10,
                "post_id": post_id,
                "msg7": {
                    "int1": 1,
                },
            },
            "comment_replies_item": f"comment-replies-item-{comment_id}",
        },
    }

    return message_to_key_urlsafe(
        message_from_json(
            {
                "msg1": {
                    "str2": "FEcomment_post_detail_page_web_replies_page",
                    "InnerCommentRepliesParams_b64": message_to_key_urlsafe(
                        message_from_json(data, InnerCommentRepliesParams),
                    ),
                },
            },
            CommentRepliesParams,
        ),
    )
