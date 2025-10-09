from http.cookiejar import MozillaCookieJar
from youtube_community_tab import Post
from youtube_community_tab.requests_handler import default_requests_handler
import time
import pytest
import os

if os.path.exists("./cookies.txt"):
    cookiejar = MozillaCookieJar("./cookies.txt")
    cookiejar.load()
    default_requests_handler.set_cookies(cookiejar)


@pytest.mark.xfail
def test_comment_actions():
    post = Post.from_post_id("UgkxJj5C3d5j0Z0FcF8S5FVMRjfP4bZIAu5e")
    comment = post.create_comment(f"[Current timestamp: {time.time()}]")

    assert comment is not None

    assert comment.add_like()
    assert comment.remove_like()

    assert comment.add_dislike()
    assert comment.remove_dislike()

    assert comment.add_heart()
    assert comment.remove_heart()

    assert comment.update(f"[Edited][Current timestamp: {time.time()}]")

    assert comment.delete()


if __name__ == "__main__":
    test_comment_actions()
