VERSION = __version__ = "0.3.0"
CLIENT_VERSION = "2.20220311.01.00"

# Regex
REGEX_YT_INITIAL_DATA = r"ytInitialData = ({(?:(?:.|\n)*)?});</script>"

# Urls
COMMUNITY_TAB_CHANNEL_ID_URL_FORMAT = "https://www.youtube.com/channel/{channel_id}/posts"  # UC6nSFpj9HTCZ5t-N3Rm3-HA
COMMUNITY_TAB_HANDLE_URL_FORMAT = "https://www.youtube.com/{handle}/posts"  # @Vsauce
COMMUNITY_TAB_LEGACY_USERNAME_URL_FORMAT = "https://www.youtube.com/c/{legacy_username}/posts"  # vsauce1
POST_URL_FORMAT = "https://www.youtube.com/post/{post_id}"
FIXED_COMMENT_URL_FORMAT = "https://www.youtube.com/post/{post_id}?lc={comment_id}"

BROWSE_ENDPOINT = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
CREATE_COMMENT_ENDPOINT = "https://www.youtube.com/youtubei/v1/comment/create_comment?prettyPrint=false"
UPDATE_COMMENT_ENDPOINT = "https://www.youtube.com/youtubei/v1/comment/update_comment?prettyPrint=false"
PERFORM_COMMENT_ACTION_ENDPOINT = "https://www.youtube.com/youtubei/v1/comment/perform_comment_action?prettyPrint=false"
