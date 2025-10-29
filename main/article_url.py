# article_urls.py - COMPLETE FIXED VERSION
from django.urls import path
from main import article_views

urlpatterns = [
    # Article URLs (public)
    path('articles/', article_views.articles_list, name='articles_list'),
    path('articles/<int:article_id>/', article_views.article_detail, name='article_detail'),
    path('articles/<int:article_id>/view/', article_views.increment_article_views, name='increment_views'),
    path('articles/<int:article_id>/download/', article_views.download_article_pdf, name='download_pdf'),

    # Article filtering URLs
    path('articles/featured/', article_views.featured_articles, name='featured_articles'),
    path('articles/open-access/', article_views.open_access_articles, name='open_access_articles'),
    path('articles/latest/', article_views.latest_articles, name='latest_articles'),
    path('articles/year/<int:year>/', article_views.articles_by_year, name='articles_by_year'),

    # Article view url
    path('articles/<int:article_id>/pdf/', article_views.ViewPDFView.as_view(), name='view_pdf'),

    # Journal URLs (public)
    path('journals/<slug:journal_slug>/', article_views.journal_detail, name='journal_detail'),

    # Issue URLs (public) - This was missing!
    path('journals/<slug:journal_slug>/<int:year>/<int:volume>/<int:number>/',
         article_views.issue_detail, name='issue_detail'),

    # Author URLs (public)
    path('authors/<int:author_id>/', article_views.author_detail, name='author_detail'),

    # Search URLs (public)
    path('search/articles/', article_views.search_articles, name='search_articles'),
]