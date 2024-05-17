# for retrieving only

from airss.chains.summarize import summarize_agent_executor_chain, chain
from airss.functions.helpers import parse_published_date
from airss.functions.images_generator import ImagesGenerator
from airss.models import RssModule, RssSource, RssModuleSettings, FetchedFeedItem, RssSummarizedContent, RssFeedSource
from airss.serializers import RssSourceSerializer, FetchedFeedItemSerializer, RssSummarizedContentSerializer

import feedparser
from bson import ObjectId


class NewsRetriever:
    def retrieve_all(self):
        results = []

        modules = RssModule.objects.all()
        for module in modules:
            result = self._module_sources(module)
            results.append(result)

        return results

    def retrieve_by_module(self, module_id: str):
        module = RssModule.objects.get(slang=module_id)
        return self._module_sources(module)

    def _module_sources(self, module: RssModule):
        results = []
        sources = RssSource.objects.filter(rss_module=module)
        for source in sources:
            module_settings = RssModuleSettings.objects.get(rss_module=module)
            result = self._retrieve_all_news(source=source, module=module, module_settings=module_settings)
            results.append(result)

        # flat_result = list(chain(*results))
        return results

    def _retrieve_all_news(self, source: RssSource, module: RssModule, module_settings: RssModuleSettings):
        serialized_source = RssSourceSerializer(source).data

        list_feed = []

        for s_source in serialized_source["sources"]:
            source_url = s_source["source_url"]
            feed = self._get_feed(source_url)
            list_feed.append({
                **feed,
                "source_url": source_url,
                "source_id": s_source["_id"],
            })

        non_filtered_feeds = self._join_feed_entries(str(source.rss_module_id), list_feed, serialized_source)

        print("GOT NON_FILTERED_FEEDS")

        self._save_fetched_news_from_rss(feeds=non_filtered_feeds, current_module=module,
                                         current_source=source,
                                         current_module_settings=module_settings)
        print("GOT _save_fetched_news_from_rss")

        all_ready_to_summarize_news = self._retrieve_fetched_feeds()

        print("GOT _retrieve_fetched_feeds")

        return all_ready_to_summarize_news

    def _get_feed(self, feed_url: str):
        return feedparser.parse(feed_url)

        # non_filtered_feeds = self._join_feed_entries(feed, serializer_data)
        # return [dict(frozenset(item.items())) for item in non_filtered_feeds]

    def _join_feed_entries(self, module_id: str, feeds: list, serializer_data):
        joined_entries = []
        for index, feed in enumerate(feeds):
            feed_source_id = serializer_data["sources"][index]["_id"]
            source_id = serializer_data['_id']
            for entry in feed["entries"]:
                joined_entries.append({
                    "data": entry,
                    "feed_module_id": module_id,
                    "feed_source_id": feed_source_id,
                    "feed_id": entry["id"]
                })
        return joined_entries

    def _save_fetched_news_from_rss(self, feeds: list, current_module: RssModule,
                                    current_module_settings: RssModuleSettings,
                                    current_source: RssSource):
        for feed in feeds:
            try:
                check_if_exist = self._is_feed_exist(feed_id=feed['feed_id'], source=current_source,
                                                     module=current_module)
                if check_if_exist is False:
                    feed_source_id = ObjectId(feed['feed_source_id'])  # Convert to ObjectId, if it's not already one
                    rss_feed_source = RssFeedSource.objects.get(_id=feed_source_id)

                    pub_date = feed['data'].get('published')
                    pub_datetime = parse_published_date(pub_date)

                    image_url = ""

                    links = feed['data'].get('links', [])

                    print(feed["data"]["title"])



                    for link in links:
                        if link['type'] == 'image/jpeg' and link['rel'] == 'enclosure':
                            image_url = link.get('href')

                    data = {
                        'feed_id': feed['feed_id'],
                        'feed_item_url': feed["data"]['link'],
                        'feed_content': feed["data"]['summary'] if 'summary' in feed["data"] else '',
                        'feed_title': feed["data"]["title"],
                        'rss_source': current_source._id,
                        'rss_module': current_module._id,
                        'rss_feed_source': rss_feed_source._id,
                        'allowed_to_summarize': current_module_settings.manual_convert is False,
                        "image_url": image_url,
                        "pub_date": pub_datetime
                    }

                    serializer = FetchedFeedItemSerializer(data=data)

                    if serializer.is_valid():
                        serializer.save(rss_source=current_source, rss_module=current_module,
                                        rss_feed_source=rss_feed_source)
                    else:
                        print("Serializer errors:", serializer.errors)
            except Exception as e:
                print(e)
                continue

    def _retrieve_fetched_feeds(self):
        list_summarized_news = []
        feeds = FetchedFeedItem.objects.all()
        for feed in feeds:
            if self._is_feed_summarized(feed):
                print("EXIST")
            else:
                print("GO TO SCRAPER BITCH " + feed.feed_title)
                feed_settings = RssModuleSettings.objects.get(rss_module=feed.rss_module)
                result = summarize_agent_executor_chain.invoke({
                    "source_id": feed.rss_feed_source._id,
                    "source_name": feed.rss_feed_source.source_name,
                    "is_require_login": feed.rss_feed_source.require_login,
                    "summarize_from_rss_feed": feed.rss_feed_source.summarize_from_rss_feed,
                    "feed_body": feed.feed_content,
                    "url": feed.feed_item_url,
                    "keywords": feed_settings.keywords,
                    "negative_keywords": feed_settings.negative_keywords,
                    "require_keywords_verification": feed.rss_feed_source.require_keywords_verification,
                    "is_manual_selection": feed_settings.manual_convert
                })

                if result is not None:
                    image_url = ""
                    image_generator = ImagesGenerator()

                    print(feed.image_url)

                    if feed.image_url:
                        image_url = image_generator.resize_image(feed.image_url)
                    else:
                        image_url = ImagesGenerator.generate_base64_image(text=result['title'])

                    rss_summarized_content = {
                        "title": result["title"],
                        "preamble": result["preamble"],
                        "text": result["news_body"],
                        "article_url": feed.feed_item_url,
                        "pub_date": feed.pub_date,
                        "image_url": image_url,
                        "fetched_feed_item": ObjectId(feed._id)
                    }
                    serializer = RssSummarizedContentSerializer(data=rss_summarized_content)
                    if serializer.is_valid():
                        serializer.save()
                        feed.is_summarized = True
                        feed.save()

                    list_summarized_news.append(result)
                else:
                    feed.is_rejected = True
                    feed.save()

        print("LEN:" + str(len(list_summarized_news)))
        return list_summarized_news

    def _is_feed_exist(self, feed_id: str, source: RssSource, module: RssModule) -> bool:
        try:
            print(feed_id)
            FetchedFeedItem.objects.get(feed_id=feed_id, rss_source=source, rss_module=module)
            return True
        except FetchedFeedItem.DoesNotExist:
            return False

    def _is_feed_summarized(self, feed: FetchedFeedItem) -> bool:
        if feed.is_summarized or feed.is_rejected or not feed.allowed_to_summarize:
            return True
        else:
            return False

