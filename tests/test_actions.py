from http import cookiejar
from youtube_community_tab.requests_handler import requests_cache
from youtube_community_tab.helpers import search_key
from youtube_community_tab import Post
import time

EXPIRATION_TIME = 24 * 60 * 60  # requests cache expiration

cookie_jar = cookiejar.MozillaCookieJar("./cookies.txt")
cookie_jar.load()
requests_cache.cookies = cookie_jar


def test_actions():
    post = Post.from_post_id("UgkxpAbrgRG3trNwPVu9ipY7vALkJ_Q-c1lv")
    comment = post.create_comment(f"[Current timestamp: {time.time()}]")

    assert comment is not None

    r = comment.set_like_comment()
    s = search_key("status", r)

    assert len(s) > 0 and s[0][1] == "STATUS_SUCCEEDED"

    r = comment.update_comment(f"[Edited][Current timestamp: {time.time()}]")
    s = search_key("status", r)

    assert len(s) > 0 and s[0][1] == "STATUS_SUCCEEDED"

    r = comment.set_dislike_comment()
    s = search_key("status", r)

    assert len(s) > 0 and s[0][1] == "STATUS_SUCCEEDED"

    r = comment.delete_comment()
    s = search_key("status", r)

    assert len(s) > 0 and s[0][1] == "STATUS_SUCCEEDED"


if __name__ == "__main__":
    test_actions()
