import json

from rest_framework import serializers
from airss.models import RSSFeedSource, RssFeedAiContent


class RSSFeedSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSSFeedSource
        fields = ('id', 'feed_source_name', 'feed_url')


class RssFeedAiContentSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(queryset=RSSFeedSource.objects.all(), many=False)

    class Meta:
        model = RssFeedAiContent
        fields = ["title", "preamble", "text", "article_url", "source", "image_url", "source_feed_id", "pub_date"]
