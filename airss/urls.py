from django.urls import path, include

from airss.views import AIRssFeedSettingsApiView, AIRssFeedApiView, AIRssGetData, AIRssFeedSettingsKeywordsApiView

urlpatterns = [
    path('feed/ai/settings/', AIRssFeedSettingsApiView.as_view()),
    path('feed/ai/settings/<str:pk>/', AIRssFeedSettingsApiView.as_view()),
    path('feed/ai/keywords/', AIRssFeedSettingsKeywordsApiView.as_view()),
    path('feed/ai/keywords/<str:pk>/', AIRssFeedSettingsKeywordsApiView.as_view()),
    path('feed/rss/ai', AIRssFeedApiView.as_view()),
    path('feed/ai', AIRssGetData.as_view())
]
