import datetime

from django_cron import CronJobBase, Schedule

from airss.helpers import create_ai_stories, is_existing_entry, get_ai_story, save_ai_story, sort_feed, get_feed
from airss.models import RSSFeedSource, RssFeedAiSettings
from airss.serializers import RSSFeedSourceSerializer
from airss.views import AIRssGetData


class FetchAiFeed:
    def do(self):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer_data = RSSFeedSourceSerializer(rss_feed_sources, many=True).data
        feed = get_feed(serializer_data)
        keywords_settings = RssFeedAiSettings.objects.all()
        filtered_feed = feed  # Optionally, you can implement filter_feed function in helpers.py
        sorted_feed = sort_feed(filtered_feed)
        ai_stories = create_ai_stories(sorted_feed, is_existing_entry, get_ai_story, save_ai_story)


class RunEveryTenMinutesCronJob(CronJobBase, FetchAiFeed):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "cron.RunEveryTenMinutesCronJob"