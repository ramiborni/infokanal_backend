from airss.models import RssModule, RssModuleSettings, RssSource


class NewsFilter:
    def __init__(self, auto_summarize: bool = False):
        self.auto_summarize = auto_summarize

    def filter(self, feeds: list, current_module: RssModule, current_module_settings: RssModuleSettings, current_source: RssSource):
        print(feeds)
