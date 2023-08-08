import time
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render
from nltk import word_tokenize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404

from airss.helpers import generate_rss_content, join_feed_entries, transform_article_with_ai, create_ai_stories, \
    sort_feed, is_existing_entry, get_ai_story, save_ai_story, get_feed
from airss.models import RSSFeedSource, RssFeedAiContent, RssFeedAiSettings
from airss.serializers import RSSFeedSourceSerializer, RssFeedAiContentSerializer, RssFeedAiSettingsSerializer

import feedparser
from bson import ObjectId


# Create your views here.

class AIRssFeedSettingsKeywordsApiView(APIView):
    def get(self, request, *args, **kwargs):
        rss_feed_settings = RssFeedAiSettings.objects.all()
        serializer = RssFeedAiSettingsSerializer(rss_feed_settings, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RssFeedAiSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        rss_feed_setting = self.get_object(pk)
        serializer = RssFeedAiSettingsSerializer(rss_feed_setting, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        rss_feed_setting = self.get_object(pk)
        rss_feed_setting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk):
        try:
                        return RssFeedAiSettings.objects.get(_id=ObjectId(pk))
        except RssFeedAiSettings.DoesNotExist:
            raise Http404

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
        rss_feed = RssFeedAiContent.objects.select_related('source').order_by('-pub_date')[:30]
        rss_content = generate_rss_content(rss_feed)

        return HttpResponse(rss_content, content_type='application/xml')


class AIRssGetData(APIView):
    def get(self, request, *args, **kwargs):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer_data = RSSFeedSourceSerializer(rss_feed_sources, many=True).data
        feed = get_feed(serializer_data)
        keywords_settings = RssFeedAiSettings.objects.all()
        filtered_feed = feed  # Optionally, you can implement filter_feed function in helpers.py
        sorted_feed = sort_feed(filtered_feed)
        ai_stories = create_ai_stories(sorted_feed, is_existing_entry, get_ai_story, save_ai_story)
        return Response(ai_stories, status=200)