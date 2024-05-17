from django.urls import path, include
from . import views
from .views import RssModuleSettingsAPI, RssSourceAPI, RssModuleAPIView, RssStatisticsView, RssModuleNewsView

urlpatterns = [
    path('feed/modules/', RssModuleAPIView.as_view(), name='rssmodule-list'),
    path('feed/modules/<str:slang>/', RssModuleAPIView.as_view(), name='rssmodule-detail'),
    path('feed/modules/<str:pk>/sources/', RssSourceAPI.as_view()),
    path('feed/modules/<str:pk>/settings/', RssModuleSettingsAPI.as_view()),
    path('feed/modules/<str:slang>/news/', RssModuleNewsView.as_view()),
    path('feed/news/', views.FetchedFeedItemDetail.as_view()),
    path('feed/rss/<str:pk>', views.AIRssFeedApiView.as_view()),
    path('feed/<str:pk>', views.AIRssGetData.as_view()),
    path('feeds/statistics', RssStatisticsView.as_view())
]
