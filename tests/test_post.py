from youtube_community_tab.post import Post

EXPIRATION_TIME = 24 * 60 * 60  # requests cache expiration


def test_post():
    post = Post.from_post_id("UgznJEQUR0fJzoMlS2Z4AaABCQ", expire_after=EXPIRATION_TIME)

    # This post can be edited, so this test can fail in the future
    post_text = post.get_text()
    expected_text = "Vsauce is 11 years old today!!!!"

    assert post_text == expected_text

    post.load_comments(expire_after=EXPIRATION_TIME)
    num_comments = len(post.comments)

    assert num_comments > 0
    assert post.comments_continuation_token

    post.load_comments(expire_after=EXPIRATION_TIME)
    num_comments_ = len(post.comments)

    assert num_comments_ > num_comments

    replied_comments = list(filter(lambda x: x.replies_continuation_token, post.comments))

    if len(replied_comments) > 0:
        test = False
        for comment in replied_comments:
            comment.load_replies(expire_after=EXPIRATION_TIME)

            if len(comment.replies) > 0:
                test = True
                break
            else:
                print("You cannot open the replies from this comment!")
                print(f"https://www.youtube.com/channel/{comment.channel_id}/community?lc={comment.comment_id}&lb={comment.post_id}")

        assert test


if __name__ == "__main__":
    test_post()
