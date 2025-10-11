from youtube_community_tab.channel import Channel


def test_community_tab():
    channel = Channel("vsauce1")

    fetched_posts = []
    for post in channel.posts():
        fetched_posts.append(post)

        if len(fetched_posts) == 20:
            break

    assert len(fetched_posts) == 20

    post = fetched_posts[-1]

    fetched_comments = []
    for comment in post.comments():
        fetched_comments.append(comment)

        if len(fetched_comments) >= 40:
            break

    assert len(fetched_comments) >= 40


if __name__ == "__main__":
    test_community_tab()
