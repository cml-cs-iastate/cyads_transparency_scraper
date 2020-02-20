from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path("bigquery", views.pull_bigquery_latest_creatives),
    path("test/<int:num>", views.test_double),
    path("test/exception", views.test_celery_exception),
    path("test/sentry-debug/", views.trigger_error),
    path("test/chrome", views.test_chrome_spawn_url),
    path("scrape", views.endpoint_scrape_new_urls),
]
