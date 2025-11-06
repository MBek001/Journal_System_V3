from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('for-publishers', views.publisher_view, name='publishers'),
    path('send-article', views.article_view, name='article'),
    path('contact', views.contact_view, name='contact'),
    path('accounts/login/', views.contact_view, name='login'),
    path('journals', views.journals_list, name='journals'),
    path('search/', views.global_search, name='global_search'),
    path('allauthors', views.authors_list, name='allauthors'),
    path('tt', views.test_diploma_view, name='testing'),

    # SEO URLs
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('robots.txt', views.robots_txt_view, name='robots'),
]
