from youtube_community_tab.comment import Comment


def test_comment():
    comment = Comment.from_ids(
        comment_id="UgyKwT4mSsABD2dCZxd4AaABAg",
        post_id="UgznJEQUR0fJzoMlS2Z4AaABCQ",
        channel_id="UC6nSFpj9HTCZ5t-N3Rm3-HA",
    )

    assert comment.get_text() == "I feel special for being one of the few people to see this lol"

    assert comment._replies_continuation_token

    comment.load_replies()

    assert len(comment.replies) > 0


if __name__ == "__main__":
    test_comment()
