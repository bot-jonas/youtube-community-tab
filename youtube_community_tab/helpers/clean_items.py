from urllib.parse import parse_qs, unquote, urlparse
from .utils import deep_get
from .utils import deep_pop


# lots of returned objects are full of tracking params, client data, duplicate info, etc. this sorta trims the fat.
def clean_content_text(content):
    for item in deep_get(content, "runs", default=[]):
        if "navigationEndpoint" in item:
            # traditional links
            if "urlEndpoint" in item["navigationEndpoint"]:
                url = item["navigationEndpoint"]["urlEndpoint"]["url"]
                # replace redirects with direct links
                if url.startswith("https://www.youtube.com/redirect"):
                    parsed_url = urlparse(url)
                    redirect_url = parse_qs(parsed_url.query)["q"][0]
                    url = unquote(redirect_url)
                item["urlEndpoint"] = {"url": url}
                item.pop("navigationEndpoint")
            # hashtags
            elif "browseEndpoint" in item["navigationEndpoint"]:
                item.pop("loggingDirectives")
                deep_pop(item, "navigationEndpoint.browseEndpoint.params")
                item["browseEndpoint"] = item["navigationEndpoint"]["browseEndpoint"]
                item["browseEndpoint"]["url"] = item["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
                item.pop("navigationEndpoint")

    return content


def clean_backstage_attachment(attachment):
    if not attachment:
        return attachment

    if "pollRenderer" in attachment:
        for choice in attachment["pollRenderer"]["choices"]:
            for value in [
                "selectServiceEndpoint",
                "deselectServiceEndpoint",
                "voteRatioIfSelected",
                "votePercentageIfSelected",
                "voteRatioIfNotSelected",
                "votePercentageIfNotSelected",
            ]:
                deep_pop(choice, value)
    elif "videoRenderer" in attachment:
        deep_pop(attachment, "videoRenderer.navigationEndpoint.watchEndpoint.watchEndpointSupportedOnesieConfig")
        attachment["videoRenderer"]["watchEndpoint"] = deep_get(attachment, "videoRenderer.navigationEndpoint.watchEndpoint", default={})
        attachment["videoRenderer"]["watchEndpoint"]["url"] = deep_get(attachment, "videoRenderer.navigationEndpoint.commandMetadata.webCommandMetadata.url")

        for long_by_line in deep_get(attachment, "videoRenderer.longBylineText.runs", default=[]):
            long_by_line["browseEndpoint"] = long_by_line["navigationEndpoint"]["browseEndpoint"]
            long_by_line.pop("navigationEndpoint")

        for short_by_line in deep_get(attachment, "videoRenderer.shortBylineText.runs", default=[]):
            short_by_line["browseEndpoint"] = short_by_line["navigationEndpoint"]["browseEndpoint"]
            short_by_line.pop("navigationEndpoint")

        for author in deep_get(attachment, "videoRenderer.ownerText.runs", default=[]):
            author["browseEndpoint"] = author["navigationEndpoint"]["browseEndpoint"]

        for value in [
            "publishedTimeText",
            "navigationEndpoint",
            "trackingParams",
            "showActionMenu",
            "menu",
            "channelThumbnailSupportedRenderers",
            "thumbnailOverlays",
        ]:
            deep_pop(attachment, f"videoRenderer.{value}")
    elif "backstageImageRenderer" in attachment:
        deep_pop(attachment, "backstageImageRenderer.trackingParams")
    elif "postMultiImageRenderer" in attachment:
        for image in attachment["postMultiImageRenderer"]["images"]:
            deep_pop(image, "backstageImageRenderer.trackingParams")

    return attachment


def clean_post_author(post_data):
    for item in post_data["authorText"]["runs"]:
        item["browseEndpoint"] = item["navigationEndpoint"]["browseEndpoint"]
        item["browseEndpoint"]["url"] = item["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        item.pop("navigationEndpoint")
    post_data["authorEndpoint"]["browseId"] = post_data["authorEndpoint"]["browseEndpoint"]["browseId"]
    author_url = post_data["authorEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    post_data["authorEndpoint"]["url"] = author_url
    for value in ["clickTrackingParams", "commandMetadata", "browseEndpoint"]:
        post_data["authorEndpoint"].pop(value)

    return post_data
