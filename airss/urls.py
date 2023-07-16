from django.urls import path, include

from airss.views import AIRssFeedSettingsApiView, AIRssFeedApiView, AIRssGetData

urlpatterns = [
    path('feed/ai/settings/', AIRssFeedSettingsApiView.as_view()),
    path('feed/ai/settings/<str:pk>/', AIRssFeedSettingsApiView.as_view()),
    path('feed/rss/ai', AIRssFeedApiView.as_view()),
    path('feed/ai', AIRssGetData.as_view())
]
