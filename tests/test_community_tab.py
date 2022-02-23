from youtube_community_tab.community_tab import CommunityTab

EXPIRATION_TIME = 24 * 60 * 60  # requests cache expiration


def test_community_tab():
    ct = CommunityTab("vsauce1")
    ct.load_posts(expire_after=EXPIRATION_TIME)

    num_posts = len(ct.posts)

    assert num_posts > 0
    assert ct.posts_continuation_token

    ct.load_posts(expire_after=EXPIRATION_TIME)
    num_posts_ = len(ct.posts)

    assert num_posts_ > num_posts

    post = ct.posts[-1]  # Choose old post to raise probability of 'good' data
    post.load_comments(expire_after=EXPIRATION_TIME)

    num_comments = len(post.comments)

    assert num_comments > 0
    assert post.comments_continuation_token

    post.load_comments(expire_after=EXPIRATION_TIME)

    num_comments_ = len(post.comments)

    assert num_comments_ > num_comments

    replied_comments = list(filter(lambda x: x.replies_continuation_token, post.comments))

    if len(replied_comments) > 0:
        comment = replied_comments[0]

        comment.load_replies(expire_after=EXPIRATION_TIME)

        assert len(comment.replies) > 0


if __name__ == "__main__":
    test_community_tab()
