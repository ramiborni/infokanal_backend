from djongo import models


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