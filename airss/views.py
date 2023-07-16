from django.http import HttpResponse
from django.shortcuts import render
from nltk import word_tokenize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404

from airss.helpers import generate_rss_content, join_feed_entries, rephrase_news_with_openai
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
        rss_feed = RssFeedAiContent.objects.all()
        sorted_feed = sorted(rss_feed, key=lambda entry: entry.pub_date, reverse=True)

        rss_content = generate_rss_content(sorted_feed)

        return HttpResponse(rss_content, content_type='application/xml')


def filter_results(feed_text: str, keywords, negative_keywords) -> bool:
    for word in word_tokenize(feed_text):
        # Check if the word matches any of the negative keywords
        if any(neg_keyword.lower() == word for neg_keyword in negative_keywords):
            return False

        # Check if the word matches any of the positive keywords
        if any(keyword == word or keyword.lower() == word or keyword.replace(' ',
                                                                             '') == word or keyword.lower() == word.replace(
            "#", "").lower() or (" " in keyword and keyword.lower() in feed_text.lower()) for keyword in keywords):
            return True

    return False


class AIRssGetData(APIView):
    def get(self, request, *args, **kwargs):
        rss_feed_sources = RSSFeedSource.objects.all()
        serializer_data = RSSFeedSourceSerializer(rss_feed_sources, many=True).data
        feed = []
        for data in serializer_data:
            feed.append(feedparser.parse(data['feed_url']))

        non_filtered_feeds = join_feed_entries(feed, serializer_data)
        final_feed = [dict(frozenset(item.items())) for item in non_filtered_feeds]

        keywords_settings = RssFeedAiSettings.objects.all()

        filtered_feed = [entry for entry in final_feed if
                         filter_results(entry['data'].get('title'), keywords_settings[0].keywords,
                                        keywords_settings[0].negative_keywords)]
        sorted_feed = sorted(filtered_feed, key=lambda entry: entry['data'].get('published_parsed'), reverse=True)

        list_ai_stories = []

        for article in sorted_feed:
            try:
                existing_entry = RssFeedAiContent.objects.get(source_feed_id=article['feed_id'])
                continue
            except RssFeedAiContent.DoesNotExist:
                existing_entry = None
            ai_story = rephrase_news_with_openai(article)
            if ai_story:
                source_id = ai_story['source_id']
                source = RSSFeedSource.objects.get(id=source_id)
                ai_story['source'] = source.id
                serializer = RssFeedAiContentSerializer(data=ai_story)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    list_ai_stories.append(ai_story)

        return Response(list_ai_stories, status=200)
