from django.urls import path
from django.views.generic import RedirectView

from . import views, admin_views

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

    # SEO URLs - Using advanced versions with Issues support and SiteSEO integration
    path('sitemap.xml', admin_views.generate_sitemap, name='sitemap'),
    path('robots.txt', admin_views.robots_txt, name='robots'),
path("favicon.ico", RedirectView.as_view(url="/static/images/favicon.ico", permanent=True)),
]
