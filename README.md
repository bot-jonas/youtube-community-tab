# youtube_community_tab

Python3 interface to YouTube community tab, it handles posts, comments and comment replies.

## Community Tab

```python
from youtube_community_tab.community_tab import CommunityTab
import json


def indent_print(text, level=1):
    indent = level * "\t"
    print(indent + ("\n" + indent).join(text.split("\n")))


# Cache expiration
EXPIRATION_TIME = 1 * 60 * 60

ct = CommunityTab("vsauce1")

# Load initial posts
ct.load_posts(expire_after=EXPIRATION_TIME)

# Load more posts
while(ct.posts_continuation_token and len(ct.posts) < 40):
    ct.load_posts(expire_after=EXPIRATION_TIME)
  
post = ct.posts[0]
print(f"[Post {post.post_id}]")
indent_print(post.get_text())

print("\n[Thumbnails]")
print(json.dumps(post.get_thumbnails()[0], indent=4))

# Load initial comments
post.load_comments(expire_after=EXPIRATION_TIME)

# Load more comments
while(post.comments_continuation_token and len(post.comments) < 100):
    post.load_comments(expire_after=EXPIRATION_TIME)
  
comment = post.comments[1]
print(f"\n[Comment {comment.comment_id}]")
indent_print(comment.get_text())

# Load initial comment replies
comment.load_replies(expire_after=EXPIRATION_TIME)

# Load more comment replies
while(comment.replies_continuation_token and len(comment.replies) < 10):
    comment.load_replies(expire_after=EXPIRATION_TIME)
  
reply = comment.replies[0]
print(f"\n[Reply {reply.reply_id}]")
indent_print(reply.get_text())

```

Output:

```
[Post UgkxzeM19x_He9LEoerdLOHwZJsqIwamUnTj]
        THANK YOU!

        WE RAISED $20,180 for the Alzheimer's Association!!!
        The winner of this beautiful cube of my beard hairs will be announced November 15th!!

        As you all know, we also donate a portion of all proceeds from the Curiosity Box to Alzheimer's research; and there's never been a better time to do a favor for your brain and everyone else's:

        RIGHT NOW: subscribe with code "BEST" and I'll send you our newest box *and* throw in our BEST-OF BOX completely FREE!!!


        https://www.curiositybox.com

[Thumbnails]
[
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s288-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 288,
        "height": 288
    },
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s400-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 400,
        "height": 400
    },
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s462-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 462,
        "height": 462
    }
]

[Comment UgyTIomDXMuKf3NTo294AaABAg]
        Thank you for doing this. Both my grandparents are affected by alzheimer's disease. It is difficult to watch a highly creative woman and an electrical engineer fade away.

[Reply UgyTIomDXMuKf3NTo294AaABAg.9TtQ3j7qvll9TtqSmVNrJu]
        Hey a heart
```

## Post

```python
from youtube_community_tab.post import Post
import json


def indent_print(text, level=1):
    indent = level * "\t"
    print(indent + ("\n" + indent).join(text.split("\n")))


# Cache expiration
EXPIRATION_TIME = 1 * 60 * 60
  
post = Post.from_post_id("UgkxzeM19x_He9LEoerdLOHwZJsqIwamUnTj")
print(f"[Post {post.post_id}]")
indent_print(post.get_text())

print("\n[Thumbnails]")
print(json.dumps(post.get_thumbnails()[0], indent=4))

# Load initial comments
post.load_comments(expire_after=EXPIRATION_TIME)

# Load more comments
while(post.comments_continuation_token and len(post.comments) < 100):
    post.load_comments(expire_after=EXPIRATION_TIME)
  
comment = post.comments[1]
print(f"\n[Comment {comment.comment_id}]")
indent_print(comment.get_text())

# Load initial comment replies
comment.load_replies(expire_after=EXPIRATION_TIME)

# Load more comment replies
while(comment.replies_continuation_token and len(comment.replies) < 10):
    comment.load_replies(expire_after=EXPIRATION_TIME)
  
reply = comment.replies[0]
print(f"\n[Reply {reply.reply_id}]")
indent_print(reply.get_text())

```

Output:
```
[Post UgkxzeM19x_He9LEoerdLOHwZJsqIwamUnTj]
        THANK YOU!

        WE RAISED $20,180 for the Alzheimer's Association!!!
        The winner of this beautiful cube of my beard hairs will be announced November 15th!!

        As you all know, we also donate a portion of all proceeds from the Curiosity Box to Alzheimer's research; and there's never been a better time to do a favor for your brain and everyone else's:

        RIGHT NOW: subscribe with code "BEST" and I'll send you our newest box *and* throw in our BEST-OF BOX completely FREE!!!


        https://www.curiositybox.com

[Thumbnails]
[
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s288-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 288,
        "height": 288
    },
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s400-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 400,
        "height": 400
    },
    {
        "url": "https://yt3.ggpht.com/DJhBHUy1SyM2XpjC1ObZyrt8llJ-qG6svLapmaZgU-wmo5rVnWR93kJMrtz85XI9EKSt395Cvziu-JE=s462-c-fcrop64=1,1e6d0000e38bffff-nd-v1",
        "width": 462,
        "height": 462
    }
]

[Comment UgyTIomDXMuKf3NTo294AaABAg]
        Thank you for doing this. Both my grandparents are affected by alzheimer's disease. It is difficult to watch a highly creative woman and an electrical engineer fade away.

[Reply UgyTIomDXMuKf3NTo294AaABAg.9TtQ3j7qvll9TtqSmVNrJu]
        Hey a heart
```

## Authentication/Membership

To access authenticated posts, like membership only posts, you need to provide cookies to authenticate your requests.

```python
from http import cookiejar
from youtube_community_tab.requests_handler import requests_cache
from youtube_community_tab.community_tab import CommunityTab

cookie_jar = cookiejar.MozillaCookieJar("cookies.txt")
cookie_jar.load()
requests_cache.cookies = cookie_jar

ct = CommunityTab("UCMwGHR0BTZuLsmjY_NT5Pwg")
ct.load_posts()

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
```
