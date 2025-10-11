from youtube_community_tab.channel import Channel


def test_community_tab():
    channel = Channel("vsauce1")
    channel.load_posts()

    num_posts = len(channel.posts)

    assert num_posts > 0
    assert channel._posts_continuation_token

    channel.load_posts()
    num_posts_ = len(channel.posts)

    assert num_posts_ > num_posts

    post = channel.posts[-1]  # Choose old post to raise probability of 'good' data
    post.load_comments()

    num_comments = len(post.comments)

    assert num_comments > 0
    assert post._comments_continuation_token

    post.load_comments()

    num_comments_ = len(post.comments)

    assert num_comments_ > num_comments


if __name__ == "__main__":
    test_community_tab()
