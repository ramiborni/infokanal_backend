import json
import time
from datetime import datetime, timedelta

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch, Exists, OuterRef, Q
from django.db.models.functions.datetime import ExtractDay
from django.http import HttpResponse
from django.shortcuts import render
from nltk import word_tokenize
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDay
import calendar

from airss.functions.retriever import NewsRetriever
from airss.functions.rss_builder import RssBuilder
from airss.models import RssModule, RssModuleSettings, RssSummarizedContent, RssSource, FetchedFeedItem, RssFeedSource
from airss.serializers import RssModuleSerializer, RssModuleSettingsSerializer, RssSourceSerializer, \
    FetchedFeedItemSerializer, MinimalFetchedFeedItemSerializer

import feedparser
from bson import ObjectId

from rest_framework import viewsets


# Create your views here.

class RssModuleAPIView(APIView):
    def get(self, request, slang=None):
        if slang:
            # Retrieve a single RssModule by slang
            rss_module = get_object_or_404(RssModule, slang=slang)
            serializer = RssModuleSerializer(rss_module)
            return Response(serializer.data)
        else:
            # Retrieve all RssModules
            rss_modules = RssModule.objects.all()
            serializer = RssModuleSerializer(rss_modules, many=True)
            return Response(serializer.data)

    def post(self, request):
        # Create a new RssModule
        serializer = RssModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slang):
        # Update an existing RssModule
        rss_module = get_object_or_404(RssModule, slang=slang)
        serializer = RssModuleSerializer(rss_module, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, slang):
        # Partially update an existing RssModule
        rss_module = get_object_or_404(RssModule, slang=slang)
        serializer = RssModuleSerializer(rss_module, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slang):
        # Delete an RssModule
        rss_module = get_object_or_404(RssModule, slang=slang)
        rss_module.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RssModuleSettingsAPI(APIView):

    def get(self, request, pk, *args, **kwargs):
        slang = pk.lower()
        try:
            rss_module_settings = RssModuleSettings.objects.get(rss_module__slang=slang)
            if rss_module_settings is None:
                return Response({'error': 'Settings Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except RssModuleSettings.DoesNotExist:
            return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RssModuleSettingsSerializer(rss_module_settings)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        slang = pk.lower()  # Get slang from request data
        if not slang:
            return Response({'error': 'Slang is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rss_module = RssModule.objects.get(slang=slang)
        except RssModule.DoesNotExist:
            return Response({'error': 'Rss Module not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RssModuleSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(rss_module=rss_module)  # Associate with found RssModule
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        slang = pk.lower()
        try:
            rss_module = RssModule.objects.get(slang=slang)
            rss_module_settings = RssModuleSettings.objects.get(rss_module=rss_module)
        except (RssModule.DoesNotExist, RssModuleSettings.DoesNotExist):
            return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        current_manual_convert = rss_module_settings.manual_convert
        serializer = RssModuleSettingsSerializer(rss_module_settings, data=request.data, partial=True)
        if serializer.is_valid():
            new_manual_convert = serializer.validated_data.get('manual_convert', current_manual_convert)

            if new_manual_convert != current_manual_convert:
                # Update all related FetchedFeedItems based on the new value of manual_convert
                new_allowed_to_summarize = not new_manual_convert
                FetchedFeedItem.objects.filter(rss_module=rss_module).update(
                    allowed_to_summarize=new_allowed_to_summarize)

            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RssSourceAPI(APIView):

    def get(self, request, pk, *args, **kwargs):
        slang = pk.lower()
        try:
            rss_module_settings = RssSource.objects.get(rss_module__slang=slang.lower())
            if rss_module_settings is None:
                return Response({'error': 'Settings Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except RssModuleSettings.DoesNotExist:
            return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RssSourceSerializer(rss_module_settings)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        try:
            rss_module = RssModule.objects.get(slang=str(pk).lower())
        except RssModule.DoesNotExist:
            return Response({"error": "RssModule not found"}, status=status.HTTP_404_NOT_FOUND)

        rss_source = RssSource(rss_module=rss_module)
        rss_source.save()

        for source_data in request.data.get('sources', []):
            rss_feed_source = RssFeedSource.objects.create(**source_data)
            rss_source.sources.add(rss_feed_source)

        rss_source.save()
        serializer = RssSourceSerializer(rss_source)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, pk, *args, **kwargs):
        slang = pk.lower()
        try:
            rss_module = RssModule.objects.get(slang=slang.lower())
            rss_source = RssSource.objects.get(rss_module=rss_module)
        except (RssModule.DoesNotExist, RssSource.DoesNotExist):
            return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RssSourceSerializer(rss_source, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIRssFeedApiView(APIView):

    def get(self, request, *args, **kwargs):
        rss_module_slang = str(kwargs.get('pk')).lower()
        rss_module = get_object_or_404(RssModule, slang=rss_module_slang)
        rss_feed = (RssSummarizedContent.objects
                    .filter(fetched_feed_item__rss_module__exact=rss_module)
                    .order_by('-pub_date')[:50])
        print(len(rss_feed))
        rss_content = RssBuilder.build_rss(slang=rss_module_slang, data=rss_feed)

        return HttpResponse(rss_content, content_type='application/xml')


class FetchedFeedItemDetail(RetrieveUpdateAPIView):
    queryset = FetchedFeedItem.objects.all()
    serializer_class = FetchedFeedItemSerializer
    lookup_field = '_id'  # Assuming you want to look up items by their _id field


class AIRssGetData(APIView):
    def get(self, request, *args, **kwargs):
        retriever = NewsRetriever()
        result = retriever.retrieve_all()
        return Response(result, status=200)


class RssStatisticsView(APIView):
    def get_summarized_content_count_from_last_month(self):
        # Get today's date
        today = timezone.now()

        # Calculate the first day of the current month
        first_day_of_current_month = today.replace(day=1)

        # Calculate the first day of the last month
        first_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = first_day_of_last_month.replace(day=1)

        # Filter RssSummarizedContent objects created from the first day of the last month
        totalSummarized = RssSummarizedContent.objects.filter(
            created_at__gte=first_day_of_last_month
        ).count()

        return totalSummarized

    def get_fetched_feed_item_count_from_last_month(self):
        # Get today's date
        today = timezone.now()

        # Calculate the first day of the current month
        first_day_of_current_month = today.replace(day=1)

        # Calculate the first day of the last month
        first_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = first_day_of_last_month.replace(day=1)

        # Filter FetchedFeedItem objects created from the first day of the last month
        total_fetched = FetchedFeedItem.objects.filter(
            pub_date__gte=first_day_of_last_month
        ).count()

        return total_fetched

    def generate_monthly_summarized_data(self):
        # Get the current date
        today = timezone.now()

        # Get the first and last day of the current month
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1], hour=23, minute=59,
                                          second=59, microsecond=999999)

        # Query RssSummarizedContent objects that might fall within the range
        summarized_contents = RssSummarizedContent.objects.filter(
            created_at__gte=first_day_of_month,
            created_at__lte=last_day_of_month
        )

        # Initialize the result list with zeros for each day of the month
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        monthly_data = [{'day': day, 'total': 0} for day in range(1, days_in_month + 1)]

        # Process each item and increment the count for the corresponding day
        for content in summarized_contents:
            if first_day_of_month <= content.created_at <= last_day_of_month:
                day_of_month = content.created_at.day
                monthly_data[day_of_month - 1]['total'] += 1

        return monthly_data

    def get(self, request, *args, **kwargs):
        total_summarized = self.get_summarized_content_count_from_last_month()
        total_fetched_news = self.get_fetched_feed_item_count_from_last_month()
        created_module = RssModule.objects.count()

        settings_subquery = RssModuleSettings.objects.filter(
            rss_module_id=OuterRef('pk'),
            manual_convert=True
        )

        # Use the subquery with Exists in the filter
        modules = RssModule.objects.prefetch_related('settings').all()

        # Manually count modules with manual_convert set to True in settings
        automated_module_count = sum(
            1 for module in modules if any(setting.manual_convert is False for setting in module.settings.all()))

        recent_news = RssSummarizedContent.objects.select_related('fetched_feed_item').order_by('-created_at')[:2]

        recent_news_data = [
            {
                'title': news.title,
                'preamble': news.preamble,
                'text': news.text,
                'article_url': news.article_url,
                'pub_date': news.pub_date,  # Format date as string
                'image_url': news.image_url,
                'created_at': news.created_at, # Format date as string
                'source': news.fetched_feed_item.rss_module.name,
            }
            for news in recent_news
        ]

        result = {
            "total_summarized": total_summarized,
            "total_fetched_news": total_fetched_news,
            "created_module": created_module,
            "automated_module": automated_module_count,
            "current_month_summarized_chart": self.generate_monthly_summarized_data(),
            "recent_news": recent_news_data
        }

        return Response(result, status=200)


class RssModuleNewsView(APIView):
    def get(self, request, slang):
        # Get the RssModule based on the slang
        rss_module = get_object_or_404(RssModule, slang=slang)

        # Fetch all news items related to that RssModule
        query = request.query_params.get('query', '')

        # Get pagination parameters from the request
        page = int(request.query_params.get('page', 1)) + 1  # front-end sends 0 in the first call when page loads
        limit = request.query_params.get('limit', 10)  # Default to 10 items per page if limit not provided
        source_name = request.query_params.get('source', None)  # Get source name from query parameters

        if source_name:
            news_items = FetchedFeedItem.objects.filter(
                rss_module=rss_module,
                feed_title__icontains=query,
                feed_content__icontains=query,
                rss_feed_source__source_name__exact=source_name
            ).order_by('-pub_date')
        else:
            news_items = FetchedFeedItem.objects.filter(
                rss_module=rss_module,
                feed_title__icontains=query,
                feed_content__icontains=query
            ).order_by('-pub_date')

        paginator = Paginator(news_items, limit)

        try:
            news_items_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            news_items_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, return an empty list.
            news_items_page = []

        # Serialize the data retrieved
        serializer = MinimalFetchedFeedItemSerializer(news_items_page, many=True)

        # Prepare the response data
        response_data = {
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'current_page': page,
            'results': serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def put(self, request, slang):
        feed_id = request.data.get('feed_id')

        fetched_feed_item = get_object_or_404(FetchedFeedItem, feed_id=feed_id)
        for attr, value in request.data.items():
            setattr(fetched_feed_item, attr, value)
        fetched_feed_item.save()

        serializer = MinimalFetchedFeedItemSerializer(fetched_feed_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
