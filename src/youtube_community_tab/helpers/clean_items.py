from urllib.parse import parse_qs, unquote, urlparse
from .utils import safely_get_value_from_key as safe
from .utils import safely_pop_value_from_key as safe_pop


# lots of returned objects are full of tracking params, client data, duplicate info, etc. this sorta trims the fat.
def clean_content_text(content):
    for item in safe(content, "runs", default=[]):
        if "navigationEndpoint" in item:
            # traditional links
            if "urlEndpoint" in item["navigationEndpoint"]:
                url = item["navigationEndpoint"]["urlEndpoint"]["url"]
                # replace redirects with direct links
                if url.startswith("https://www.youtube.com/redirect"):
                    parsed_url = urlparse(item["navigationEndpoint"]["urlEndpoint"]["url"])
                    redirect_url = parse_qs(parsed_url.query)["q"][0]
                    item["urlEndpoint"] = {"url": unquote(redirect_url)}
                item.pop("navigationEndpoint")
            # hashtags
            elif "browseEndpoint" in item["navigationEndpoint"]:
                item.pop("loggingDirectives")
                safe_pop(item, "navigationEndpoint", "browseEndpoint", "params")
                item["browseEndpoint"] = item["navigationEndpoint"]["browseEndpoint"]
                item["browseEndpoint"]["url"] = item["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
                item.pop("navigationEndpoint")
    return content


def clean_backstage_attachement(attachment):
    if attachment:
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
                    safe_pop(choice, value)
        elif "videoRenderer" in attachment:
            safe_pop(attachment, "videoRenderer", "navigationEndpoint", "watchEndpoint", "watchEndpointSupportedOnesieConfig")
            attachment["videoRenderer"]["watchEndpoint"] = safe(attachment, "videoRenderer", "navigationEndpoint", "watchEndpoint", default={})
            attachment["videoRenderer"]["watchEndpoint"]["url"] = safe(
                attachment, "videoRenderer", "navigationEndpoint", "commandMetadata", "webCommandMetadata", "url"
            )

            for long_by_line in safe(attachment, "videoRenderer", "longBylineText", "runs", default=[]):
                long_by_line["browseEndpoint"] = long_by_line["navigationEndpoint"]["browseEndpoint"]
                long_by_line.pop("navigationEndpoint")

            for short_by_line in safe(attachment, "videoRenderer", "shortBylineText", "runs", default=[]):
                short_by_line["browseEndpoint"] = short_by_line["navigationEndpoint"]["browseEndpoint"]
                short_by_line.pop("navigationEndpoint")

            for author in safe(attachment, "videoRenderer", "ownerText", "runs", default=[]):
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
                safe_pop(attachment, "videoRenderer", value)
        return attachment
    return None
