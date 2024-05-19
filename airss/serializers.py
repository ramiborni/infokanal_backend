import json

from bson import ObjectId
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from airss.models import RssModule, RssModuleSettings, RssSource, FetchedFeedItem, RssSummarizedContent, RssFeedSource


class ObjectIdFieldSerializer(serializers.Field):
    """Serializer field for Django models ObjectIdField."""

    def to_internal_value(self, data):
        try:
            # Convert the incoming value to ObjectId
            return ObjectId(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError('This field must be a valid ObjectId.')

    def to_representation(self, value):
        # Convert ObjectId to string for serialization
        if isinstance(value, ObjectId):
            return str(value)
        return value


class JSONSerializerField(serializers.Field):
    """Serializer for JSON data."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                # Parse the string to Python native data type
                return json.loads(data)
            except ValueError as e:
                raise serializers.ValidationError(f"Invalid JSON format: {e}")
        return data

    def to_representation(self, value):
        if isinstance(value, str):
            try:
                # Convert string stored in database to Python native data type for JSON rendering
                return json.loads(value)
            except ValueError:
                return value
        return value


class RssModuleSerializer(serializers.ModelSerializer):
    # Nested Serializers
    settings = serializers.SerializerMethodField()
    rss_sources = serializers.SerializerMethodField()

    class Meta:
        model = RssModule
        fields = ['_id', 'name', 'slang', 'created_at', 'updated_at', 'settings', 'rss_sources']
        read_only_fields = ['_id']

    def get_settings(self, obj):
        settings = RssModuleSettings.objects.filter(rss_module=obj).first()
        return RssModuleSettingsSerializer(settings).data if settings else None

    def get_rss_sources(self, obj):
        rss_sources = RssSource.objects.filter(rss_module=obj).first()
        return RssSourceSerializer(rss_sources).data if rss_sources else None

    def create(self, validated_data):
        validated_data['slang'] = validated_data.get('slang', '').lower()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['slang'] = validated_data.get('slang', '').lower()
        return super().update(instance, validated_data)


class RssModuleSettingsSerializer(serializers.ModelSerializer):
    manual_convert = JSONSerializerField()
    keywords = JSONSerializerField()
    negative_keywords = JSONSerializerField()

    class Meta:
        model = RssModuleSettings
        fields = ['manual_convert', 'keywords', 'negative_keywords']


class RssFeedSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RssFeedSource
        fields = ['_id', 'source_url', 'require_login', 'summarize_from_rss_feed', "source_name"]
        read_only_fields = ['_id']


class RssSourceSerializer(serializers.ModelSerializer):
    sources = RssFeedSourceSerializer(many=True)

    class Meta:
        model = RssSource
        fields = ['_id', 'sources', 'created_at', 'updated_at']
        read_only_fields = ['_id']

    def update(self, instance, validated_data):
        # Update simple fields
        instance.updated_at = validated_data.get('updated_at', instance.updated_at)
        instance.save()

        # Handle the nested 'sources' data
        sources_data = validated_data.pop('sources', [])
        current_source_ids = set([source._id for source in instance.sources.all()])
        new_source_ids = set([source_data.get('_id') for source_data in sources_data if source_data.get('_id')])

        # Remove sources that are not in the new list
        for source_id in current_source_ids - new_source_ids:
            instance.sources.remove(RssFeedSource.objects.get(_id=source_id))

        # Add new sources or update existing ones
        for source_data in sources_data:
            source_id = source_data.get('_id', None)
            if source_id:
                rss_feed_source = RssFeedSource.objects.get(_id=source_id)
                rss_feed_source_serializer = RssFeedSourceSerializer(rss_feed_source, data=source_data, partial=True)
                if rss_feed_source_serializer.is_valid():
                    rss_feed_source_serializer.save()
                instance.sources.add(rss_feed_source)
            else:
                # Create new RssFeedSource if _id is not provided
                rss_feed_source = RssFeedSource.objects.create(**source_data)
                instance.sources.add(rss_feed_source)

        return instance


class FetchedFeedItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = FetchedFeedItem
        fields = ['_id', 'feed_id', 'feed_item_url', 'feed_content', 'allowed_to_summarize', 'rss_source', 'rss_module',
                  'feed_title',
                  'image_url',
                  'rss_feed_source', 'pub_date']
        read_only_fields = ['_id']


class MinimalFetchedFeedItemSerializer(serializers.ModelSerializer):
    rss_feed_source = RssFeedSourceSerializer()

    class Meta:
        model = FetchedFeedItem
        fields = ['feed_id', 'feed_item_url','feed_title','pub_date', 'feed_content', 'allowed_to_summarize', 'image_url',
                  'rss_feed_source']


class RssSummarizedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RssSummarizedContent
        fields = ['title', 'preamble', 'text', 'article_url', 'pub_date', 'image_url', 'created_at',
                  'fetched_feed_item']

        read_only_fields = ['created_at']


'''

class RSSFeedSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSSFeedSource
        fields = ('id', 'feed_source_name', 'feed_url')


class RssFeedAiContentSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(queryset=RSSFeedSource.objects.all(), many=False)

    class Meta:
        model = RssFeedAiContent
        fields = ["title", "preamble", "text", "article_url", "source", "image_url", "source_feed_id", "pub_date"]


class RssFeedAiSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RssFeedAiSettings
        fields = ['_id', 'keywords', 'negative_keywords']


class FetchedNewsSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(queryset=RSSFeedSource.objects.all(), many=False)

    class Meta:
        model = FetchedNews
        fields = ['source', 'feed_id']


'''
