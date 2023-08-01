import time
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render
from nltk import word_tokenize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404

from airss.helpers import generate_rss_content, join_feed_entries, transform_article_with_ai
from airss.models import RSSFeedSource, RssFeedAiContent, RssFeedAiSettings
from airss.serializers import RSSFeedSourceSerializer, RssFeedAiContentSerializer

import feedparser


# Create your views here.

class AIRssFeedSettingsApiView(APIView):

    def get(self, request, *args, **kwargs):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer = RSSFeedSourceSerializer(rss_feed_sources, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RSSFeedSourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        rss_feed_source = self.get_object(pk)
        serializer = RSSFeedSourceSerializer(rss_feed_source, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        rss_feed_source = self.get_object(pk)
        rss_feed_source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk):
        try:
            return RSSFeedSource.objects.get(pk=pk)
        except RSSFeedSource.DoesNotExist:
            raise Http404

class AIRssFeedApiView(APIView):

    def get(self, request, *args, **kwargs):
        rss_feed = RssFeedAiContent.objects.select_related('source').all()
        sorted_feed = sorted(rss_feed, key=lambda entry: entry.pub_date, reverse=True)
        rss_content = generate_rss_content(sorted_feed)

        return HttpResponse(rss_content, content_type='application/xml')


class AIRssGetData(APIView):
    def get(self, request, *args, **kwargs):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer_data = RSSFeedSourceSerializer(rss_feed_sources, many=True).data
        feed = self.get_feed(serializer_data)
        keywords_settings = RssFeedAiSettings.objects.all()
        filtered_feed = feed #self.filter_feed(feed, keywords_settings[0])
        sorted_feed = self.sort_feed(filtered_feed)
        ai_stories = self.create_ai_stories(sorted_feed)
        return Response(ai_stories, status=200)

    def get_feed(self, serializer_data):
        feed = []
        for data in serializer_data:
            feed.append(feedparser.parse(data['feed_url']))
        non_filtered_feeds = join_feed_entries(feed, serializer_data)
        return [dict(frozenset(item.items())) for item in non_filtered_feeds]

    def sort_feed(self, feed):
        def sort_key(entry):
            published_parsed = entry['data'].get('published_parsed')
            return datetime.fromtimestamp(time.mktime(published_parsed)) if published_parsed else datetime.min
        return sorted(feed, key=sort_key, reverse=True)

    def create_ai_stories(self, sorted_feed):
        list_ai_stories = []
        for article in sorted_feed:
            if self.is_existing_entry(article):
                continue
            ai_story = self.get_ai_story(article)
            if ai_story:
                self.save_ai_story(ai_story)
                list_ai_stories.append(ai_story)
        return list_ai_stories

    def is_existing_entry(self, article):
        try:
            RssFeedAiContent.objects.get(source_feed_id=article['feed_id'])
            return True
        except RssFeedAiContent.DoesNotExist:
            return False

    def get_ai_story(self, article):
        method_name = article['feed_source_name']  # Assuming 'feed_source_name' is the method name
        return transform_article_with_ai(article, method_name)

    def save_ai_story(self, ai_story):
        source_id = ai_story['source_id']
        source = RSSFeedSource.objects.get(id=source_id)
        ai_story['source'] = source.id
        serializer = RssFeedAiContentSerializer(data=ai_story)
        if serializer.is_valid(raise_exception=True):
            serializer.save()