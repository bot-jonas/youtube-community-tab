from http import cookiejar
from youtube_community_tab.requests_handler import requests_cache
from youtube_community_tab.community_tab import CommunityTab
from youtube_community_tab import Post

EXPIRATION_TIME = 24 * 60 * 60  # requests cache expiration

cookie_jar = cookiejar.MozillaCookieJar("./cookies.txt")
cookie_jar.load()
requests_cache.cookies = cookie_jar


def test_load_membership_posts():
    ct = CommunityTab("UCevD0wKzJFpfIkvHOiQsfLQ")

    membership_post = None
    while ct.posts_continuation_token is not False:
        ct.load_posts(expire_after=EXPIRATION_TIME)

        for post in ct.posts:
            if post.sponsor_only_badge is not None:
                membership_post = post
                break

        if membership_post is not None:
            break

    assert membership_post is not None


def test_membership_post():
    post = Post.from_post_id("UgkxYPXcG8gdCetpwXlU2ymJawN29rRew_hy", expire_after=EXPIRATION_TIME)

    # This post can be edited, so this test can fail in the future
    post_text = post.get_text()

    expected_text = "\u5148\u65e5\u306f\u30aa\u30ea\u30b8\u30ca\u30eb\u7d75\u6587\u5b57\uff08\u8349\uff09\u306e\u30ea\u30af\u30a8\u30b9\u30c8\u3042\u308a\u304c\u3068\u3046\u3054\u3056\u3044\u307e\u3057\u305f\uff01\n\u3044\u307e\u306f\u308f\u305f\u3057\uff08\u305f\u307e\uff09\u304c\u5165\u308c\u305f\u3044\u3082\u306e\u3092\u4e3b\u306b\u5165\u308c\u3066\u3044\u308b\u306e\u3067\u3001\n\u4e0d\u5b9a\u671f\u3067\u30a2\u30f3\u30b1\u30fc\u30c8\u3092\u4f7f\u3063\u3066\u4f7f\u7528\u983b\u5ea6\u306e\u4f4e\u3044\u3082\u306e\u3092\u5165\u308c\u66ff\u3048\u3088\u3046\u304b\u30ca\u30fc\u306a\u3093\u3066\u8003\u3048\u3066\u3044\u307e\u3059\uff01\n\n\u30e1\u30f3\u30d0\u30fc\u30b7\u30c3\u30d7\u3092\u958b\u8a2d\u3059\u308b\u3068\u304d\u306b\u5f35\u308a\u5207\u3063\u306620\u500b\u4ee5\u4e0a\u4f5c\u3063\u305f\u3093\u3067\u3059\u304c\u3001\n\u53c2\u52a0\u30e1\u30f3\u30d0\u30fc\u306e\u6570\u3067\u767b\u9332\u4e0a\u9650\u304c\u5897\u3048\u308b\u3053\u3068\u77e5\u3089\u306a\u304b\u3063\u305f\u3093\u3067\u3059\u3088\u306d\u30fc\u2026\uff83\uff9e\uff7d\uff96\uff88\uff70\u2026\n\u3053\u3061\u3089\u306e\u6295\u7a3f\u3084\u3072\u306a\u305f\u306e\u96d1\u8ac7\u306a\u3093\u304b\u3067\u30ea\u30af\u30a8\u30b9\u30c8\u3082\u3089\u3048\u308b\u3068\u5b09\u3057\u3044\u3067\u3059\uff01\n\n\u3067\u306f\u3067\u306f\uff01\u4e5d\u77f3\u305f\u307e\u3067\u3057\u305f\u2606\u307e\u3063\u305f\u306d\uff5e\uff01"

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
