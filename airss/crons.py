import datetime

from django_cron import CronJobBase, Schedule

from airss.helpers import create_ai_stories, is_existing_entry, get_ai_story, save_ai_story, sort_feed, get_feed
from airss.models import RSSFeedSource, FetchedNews
from airss.serializers import RSSFeedSourceSerializer

class FetchAiFeed:
    def do(self):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer_data = RSSFeedSourceSerializer(rss_feed_sources, many=True).data
        feed = get_feed(serializer_data)
        filtered_feed = feed  # Optionally, you can implement filter_feed function in helpers.py
        sorted_feed = sort_feed(filtered_feed)
        list_feed_scrapped = FetchedNews.objects.all()
        ai_stories = create_ai_stories(sorted_feed, is_existing_entry, get_ai_story, save_ai_story,list_feed_scrapped)



class RunEveryTenMinutesCronJob(CronJobBase, FetchAiFeed):
    RUN_EVERY_MINS = 10
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "cron.RunEveryTenMinutesCronJob"
