from http import cookiejar
from youtube_community_tab.requests_handler import requests_cache
from youtube_community_tab.community_tab import CommunityTab
from youtube_community_tab import Post

EXPIRATION_TIME = 24 * 60 * 60  # requests cache expiration

cookie_jar = cookiejar.MozillaCookieJar("./cookies.txt")
cookie_jar.load()
requests_cache.cookies = cookie_jar


def test_load_membership_posts():
    ct = CommunityTab("UCMwGHR0BTZuLsmjY_NT5Pwg")
    ct.load_posts(expire_after=EXPIRATION_TIME)

    membership_post = None
    while ct.posts_continuation_token:
        for post in ct.posts:
            if post.sponsor_only_badge is not None:
                membership_post = post
                break

        if(membership_post is not None):
            break

        ct.load_posts(expire_after=EXPIRATION_TIME)

    assert(membership_post is not None)


def test_membership_post():
    post = Post.from_post_id("UgkxJYrBY-QqIt1ysrZY0ZP84SGJLWmDmtoU", expire_after=EXPIRATION_TIME)

    # This post can be edited, so this test can fail in the future
    post_text = post.get_text()

    expected_text = "Cheeeeeeeeeeeeeeeese\nAm I bored? I don't know.... nyeh 😺"

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
        comment = replied_comments[0]

        comment.load_replies(expire_after=EXPIRATION_TIME)

        assert len(comment.replies) > 0


if __name__ == "__main__":
    test_load_membership_posts()
    test_membership_post()
