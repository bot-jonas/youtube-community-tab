from ...utils import message_to_key_urlsafe, message_from_json
from .fixed_comment_params_pb2 import FixedCommentParams, InnerFixedCommentParams


def fixed_comment_params(comment_id, post_id, channel_id):
    return message_to_key_urlsafe(
        message_from_json(
            {
                "msg1": {
                    "str1": "FEcomment_post_detail_page_web_top_level",
                    "InnerFixedCommentParams_b64": message_to_key_urlsafe(
                        message_from_json(
                            {
                                "str2": "posts",
                                "msg2": {
                                    "msg4": {
                                        "int1": 0,
                                        "comment_id": comment_id,
                                        "int2": 1,
                                        "post_id": post_id,
                                        "channel_id": channel_id,
                                    },
                                    "str3": "comments-section",
                                },
                                "msg3": {
                                    "channel_id": channel_id,
                                    "post_id": post_id,
                                    "comment_id": comment_id,
                                    "channel_id2": channel_id,
                                },
                            },
                            InnerFixedCommentParams,
                        ),
                    ),
                },
            },
            FixedCommentParams,
        ),
    )
