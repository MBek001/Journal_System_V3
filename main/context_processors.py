from .models import Journal, Article, SiteSEO


def site_context(request):
    return {
        'site_name': 'Imfaktor',
        'site_description': 'Ilmiy Nashrlar Portali',
        'total_articles': Article.objects.count(),
        'total_journals': Journal.objects.filter(is_active=True).count(),
    }

def seo_context(request):
    return {'site_seo': SiteSEO.objects.first()}