from ...utils import message_to_key_urlsafe, message_from_json
from .perform_comment_action_params_pb2 import PerformCommentActionParams
from enum import Enum


class CommentAction(Enum):
    ADD_LIKE = "ADD_LIKE"
    REMOVE_LIKE = "REMOVE_LIKE"
    ADD_DISLIKE = "ADD_DISLIKE"
    REMOVE_DISLIKE = "REMOVE_DISLIKE"
    ADD_HEART = "ADD_HEART"
    REMOVE_HEART = "REMOVE_HEART"
    DELETE = "DELETE"

    def get_constants(self):
        match self:
            case CommentAction.ADD_LIKE:
                return (5, 0)
            case CommentAction.REMOVE_LIKE:
                return (5, 1)
            case CommentAction.ADD_DISLIKE:
                return (4, 0)
            case CommentAction.REMOVE_DISLIKE:
                return (4, 1)
            case CommentAction.ADD_HEART:
                return (14, None)
            case CommentAction.REMOVE_HEART:
                return (15, None)
            case CommentAction.DELETE:
                return (6, None)


def perform_comment_action_params(comment_id, post_id, channel_id, action: CommentAction):
    data = {
        "int1": 7,
        "comment_id": comment_id,
        "int2": 0,
        "int3": 1,
        "post_id": post_id,
        "channel_id": channel_id,
        "int4": 0,
        "int5": 1,
    }

    (action, action_variant) = action.get_constants()

    data["action"] = action
    if action_variant is not None:
        data["action_variant"] = action_variant

    return message_to_key_urlsafe(message_from_json(data, PerformCommentActionParams))
