from youtube_community_tab.post import Post


def test_post():
    post = Post.from_post_id("UgznJEQUR0fJzoMlS2Z4AaABCQ")

    # This post can be edited, so this test can fail in the future
    post_text = post.get_text()
    expected_text = "Vsauce is 11 years old today!!!!"

    assert post_text == expected_text

    fetched_comments = []
    for comment in post.comments():
        fetched_comments.append(comment)

        if len(fetched_comments) >= 40:
            break

    assert len(fetched_comments) >= 40

    there_is_a_replied_comment = False
    for comment in fetched_comments:
        replies = list(comment.replies())

        if len(replies) > 0:
            there_is_a_replied_comment = True
            break

    assert there_is_a_replied_comment


if __name__ == "__main__":
    test_post()
