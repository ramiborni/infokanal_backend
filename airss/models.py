from datetime import datetime

import bson
from bson import ObjectId
from djongo import models
from rest_framework.fields import BooleanField

'''

class RSSFeedSource(models.Model):
    feed_source_name = models.CharField(max_length=100)
    feed_url = models.URLField()
    require_login= models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.feed_source_name


class RssFeedAiContent(models.Model):
    title = models.CharField(max_length=500)
    preamble = models.CharField(max_length=2500)
    text = models.CharField(max_length=5000)
    article_url = models.URLField()
    pub_date = models.DateTimeField(null=False)
    image_url = models.TextField()
    createdat = models.DateTimeField(auto_now=True)
    source_feed_id = models.CharField(max_length=500, unique=True)
    source = models.ForeignKey(RSSFeedSource, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class RssFeedAiSettings(models.Model):
    _id = models.ObjectIdField()
    keywords = models.JSONField(default=[])
    negative_keywords = models.JSONField(default=[])


class FetchedNews(models.Model):
    _id = models.ObjectIdField()
    source = models.ForeignKey(RSSFeedSource, on_delete=models.CASCADE)
    feed_id = models.TextField()
    
'''


class RssModule(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    name = models.TextField(unique=True)
    slang = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class RssModuleSettings(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    manual_convert = models.BooleanField(default=False)
    keywords = models.JSONField(default=[])
    negative_keywords = models.JSONField(default=[])
    rss_module = models.ForeignKey(RssModule, on_delete=models.CASCADE, related_name='settings')


class RssFeedSource(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    source_name = models.TextField(default="")
    source_url = models.URLField() # must only rss url
    require_login = models.BooleanField(default=False) # require login to get article/news
    summarize_from_rss_feed = models.BooleanField(default=False) # Use only article mentioned/written in the Rss feed without browsing/scrapping the website
    require_keywords_verification = models.BooleanField(default=True)


class RssSource(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    sources = models.ManyToManyField(RssFeedSource)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    rss_module = models.ForeignKey(RssModule, on_delete=models.CASCADE)


class FetchedFeedItem(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    feed_id = models.TextField()  # ID that got from the feed to compare between fetched feeds
    feed_title = models.TextField(default="")
    feed_item_url = models.URLField()
    feed_content = models.TextField(default='', blank=True)
    allowed_to_summarize = models.BooleanField(default=True)
    is_summarized = models.BooleanField(default=False) # true after summarizing
    is_rejected = models.BooleanField(default=False) # true after rejecting to summarize due to keywords
    rss_feed_source = models.ForeignKey(RssFeedSource, on_delete=models.CASCADE, default="")
    image_url = models.TextField(default="", blank=True)
    rss_source = models.ForeignKey(RssSource, on_delete=models.CASCADE)
    rss_module = models.ForeignKey(RssModule, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(null=False)


class RssSummarizedContent(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    title = models.CharField(max_length=500)
    preamble = models.CharField(max_length=2500)
    text = models.CharField(max_length=5000)
    article_url = models.URLField()
    pub_date = models.DateTimeField(null=False)
    image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    fetched_feed_item = models.ForeignKey(FetchedFeedItem, on_delete=models.CASCADE, default="")