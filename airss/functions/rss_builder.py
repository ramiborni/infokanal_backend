from datetime import datetime

from feedgen.feed import FeedGenerator
import pytz

from airss.models import RssSummarizedContent


class RssBuilder:

    @staticmethod
    def build_rss(slang: str, data: list[RssSummarizedContent]):
        fg = FeedGenerator()
        fg.load_extension("media", rss=True)
        fg.id('https://www.infokanal.com/feed/rss/' + slang)
        fg.title('infokanal RSS feed')
        fg.link(href='https://www.infokanal.com/feed/rss/' + slang)
        fg.description('infokanal RSS feed')
        oslo_timezone = pytz.timezone('Europe/Oslo')
        fg.lastBuildDate(datetime.now(tz=oslo_timezone))

        for entry in data:
            fe = fg.add_entry()
            if entry.fetched_feed_item.feed_id:
                fe.id(entry.fetched_feed_item.feed_id)
            if entry.title:
                fe.title(entry.title)
            if entry.article_url:
                fe.link(href=entry.article_url, rel='alternate')
            if entry.preamble:
                fe.summary(entry.preamble)
            if entry.text:
                fe.content(
                    entry.text + f"\nSaken var først omtalt på - {entry.fetched_feed_item.rss_feed_source.source_name}")
            if entry.pub_date:
                pub_date = entry.pub_date.astimezone(oslo_timezone)
                fe.pubDate(pub_date)
            if entry.image_url:
                fe.enclosure(entry.image_url, 0, 'image/jpeg')
                fe.media.thumbnail({'url': entry.image_url, 'width': '200'},
                                   group=None)
                fe.media.content({'url': entry.image_url, 'width': '400'},
                                 group=None)

        rss_str = fg.rss_str(pretty=True)
        return rss_str
