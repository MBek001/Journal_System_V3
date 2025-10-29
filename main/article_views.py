from django.shortcuts import render, get_object_or_404
import os
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import F
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Article, Author, Journal, Issue, JournalPolicy, JournalEditor


class ViewPDFView(View):

    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)

        # Check if PDF exists
        if not article.main_pdf or not article.main_pdf.file:
            raise Http404("PDF file not found")

        try:
            # Access the file field from the File model
            pdf_file = article.main_pdf.file

            # Open and read the PDF file
            with pdf_file.open('rb') as pdf:
                response = HttpResponse(pdf.read(), content_type='application/pdf')

                response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_file.name)}"'

                response['Cache-Control'] = 'public, max-age=3600'

                return response

        except (FileNotFoundError, ValueError) as e:
            raise Http404("PDF file not found")


def view_pdf(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # Check if PDF exists
    if not article.main_pdf or not article.main_pdf.file:
        raise Http404("PDF file not found")

    try:
        # Access the file field from the File model
        pdf_file = article.main_pdf.file

        # Open and read the PDF file
        with pdf_file.open('rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(pdf_file.name)}"'
            response['Cache-Control'] = 'public, max-age=3600'
            return response

    except (FileNotFoundError, ValueError) as e:
        raise Http404("PDF file not found")


def article_detail(request, article_id):
    """Display individual article with SEO optimization"""
    try:
        article = get_object_or_404(
            Article.objects.select_related('issue__journal', 'main_pdf')
            .prefetch_related('authors'),
            id=article_id,
            is_published=True
        )

        # Increment view count
        article.increment_views()

        # Get related articles from same journal
        related_articles = Article.objects.filter(
            issue__journal=article.issue.journal,
            is_published=True
        ).exclude(id=article.id).order_by('-date_published')[:5] if article.issue else []

        # Get other articles by same authors
        author_articles = Article.objects.filter(
            authors__in=article.authors.all(),
            is_published=True
        ).exclude(id=article.id).distinct().order_by('-date_published')[:3]

        context = {
            'article': article,
            'related_articles': related_articles,
            'references': article.references or '',
            'author_articles': author_articles,
            'page_title': f'{article.title} - Imfaktor',
            'meta_description': article.meta_description or article.abstract[:160] if article.abstract else '',
            'keywords': [k.strip() for k in (article.keywords or '').split(',') if k.strip()],
        }

        return render(request, 'article_detail.html', context)

    except Article.DoesNotExist:
        raise Http404("Maqola topilmadi")


def articles_list(request):
    """Display all articles with pagination and search"""
    search_query = request.GET.get('search', '')
    journal_filter = request.GET.get('journal', '')
    year_filter = request.GET.get('year', '')

    articles = Article.objects.filter(is_published=True).select_related('issue__journal').prefetch_related('authors')

    # Apply filters
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(abstract__icontains=search_query) |
            Q(keywords__icontains=search_query) |
            Q(authors__first_name__icontains=search_query) |
            Q(authors__last_name__icontains=search_query)
        ).distinct()

    if journal_filter:
        articles = articles.filter(issue__journal__id=journal_filter)

    if year_filter:
        articles = articles.filter(date_published__year=year_filter)

    articles = articles.order_by('-date_published')

    # Pagination
    paginator = Paginator(articles, 12)  # 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filters for template
    journals = Journal.objects.filter(is_active=True)
    years = Article.objects.filter(is_published=True).dates('date_published', 'year', order='DESC')

    context = {
        'articles': page_obj,
        'journals': journals,
        'years': years,
        'search_query': search_query,
        'journal_filter': journal_filter,
        'year_filter': year_filter,
        'page_title': 'Barcha Maqolalar - Imfaktor',
    }

    return render(request, 'articles_list.html', context)


def journal_detail(request, journal_slug):
    """Display journal with current active issue and organized sections"""
    journal = get_object_or_404(Journal, url_slug=journal_slug, is_active=True)

    # Get current active issue
    current_issue = Issue.objects.filter(
        journal=journal,
        is_active=True,
        is_published=True
    ).first()

    # Get articles for current issue
    current_articles = []
    if current_issue:
        current_articles = Article.objects.filter(
            issue=current_issue,
            is_published=True
        ).select_related('issue').prefetch_related('authors').order_by('-date_published')

    # Get all issues for statistics
    all_issues = Issue.objects.filter(journal=journal, is_published=True)

    # Get all articles for statistics
    all_articles = Article.objects.filter(
        issue__journal=journal,
        is_published=True
    ).select_related('issue').prefetch_related('authors')

    # Get archived issues (inactive)
    archived_issues = Issue.objects.filter(
        journal=journal,
        is_active=False,
        is_published=True
    ).order_by('-year', '-volume', '-number')

    # Get journal editors (ordered by editor type and order)
    editors = JournalEditor.objects.filter(
        journal_id=journal.id,
        is_active=True
    ).order_by( 'editor_type', 'last_name', 'first_name')

    # Get journal policies (active and public only)
    policies = JournalPolicy.objects.filter(
        journal=journal,
        is_active=True,
        is_public=True
    ).order_by('order', 'policy_type')

    # Group editors by type for better display
    editors_by_type = {}
    for editor in editors:
        editor_type = editor.get_editor_type_display()
        if editor_type not in editors_by_type:
            editors_by_type[editor_type] = []
        editors_by_type[editor_type].append(editor)

    # Pagination for current articles
    paginator = Paginator(current_articles, 10)
    page_number = request.GET.get('page')
    current_articles_page = paginator.get_page(page_number)

    context = {
        'journal': journal,
        'current_issue': current_issue,
        'current_articles': current_articles_page,
        'all_issues_count': all_issues.count(),
        'all_articles_count': all_articles.count(),
        'archived_issues': archived_issues,
        'editors': editors,
        'editors_by_type': editors_by_type,
        'policies': policies,
        'page_title': f'{journal.title} - Imfaktor',
        'meta_description': journal.meta_description or journal.description[:160] if journal.description else '',
    }

    return render(request, 'journal_detail.html', context)


def issue_detail(request, journal_slug, year, volume, number):
    """Display issue with its articles"""
    journal = get_object_or_404(Journal, url_slug=journal_slug, is_active=True)
    issue = get_object_or_404(
        Issue,
        journal=journal,
        year=year,
        volume=volume,
        number=number,
        is_published=True
    )

    # Get issue articles
    articles = Article.objects.filter(
        issue=issue,
        is_published=True
    ).prefetch_related('authors').order_by('first_page', 'created_at')

    context = {
        'journal': journal,
        'issue': issue,
        'articles': articles,
        'page_title': f'{issue.full_citation} - {journal.title} - Imfaktor',
        'meta_description': issue.meta_description or issue.description[:160] if issue.description else '',
    }

    return render(request, 'issue_detail.html', context)


def author_detail(request, author_id):
    """Display author profile with their articles"""
    author = get_object_or_404(Author, id=author_id, is_active=True)

    # Get author's articles
    articles = Article.objects.filter(
        authors=author,
        is_published=True
    ).select_related('issue__journal').order_by('-date_published')

    # Get statistics
    total_articles = articles.count()
    total_views = sum(article.views for article in articles)
    total_citations = 0  # You can implement citation counting

    context = {
        'author': author,
        'articles': articles,
        'total_articles': total_articles,
        'total_views': total_views,
        'total_citations': total_citations,
        'page_title': f'{author.full_name} - Imfaktor',
        'meta_description': author.bio[
                            :160] if author.bio else f'{author.full_name} - Imfaktor portalidagi muallif profili',
    }

    return render(request, 'author_detail.html', context)


@require_POST
def increment_article_views(request, article_id):
    """AJAX endpoint to increment article view count"""
    try:
        article = get_object_or_404(Article, id=article_id, is_published=True)
        article.increment_views()
        return JsonResponse({'success': True, 'views': article.views})

    except Article.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Article not found'})


def search_articles(request):
    """AJAX search for articles"""
    query = request.GET.get('q', '')

    if len(query) < 3:
        return JsonResponse({'results': []})

    articles = Article.objects.filter(
        Q(title__icontains=query) |
        Q(abstract__icontains=query) |
        Q(keywords__icontains=query),
        is_published=True
    ).select_related('issue__journal').prefetch_related('authors')[:10]

    results = []
    for article in articles:
        authors = [author.full_name for author in article.authors.all()]
        results.append({
            'id': article.id,
            'title': article.title,
            'authors': ', '.join(authors),
            'journal': article.issue.journal.title if article.issue else '',
            'date': article.date_published.strftime('%Y'),
            'url': f'/articles/{article.id}/'
        })

    return JsonResponse({'results': results})


def download_article_pdf(request, article_id):
    """Handle PDF download with tracking"""
    article = get_object_or_404(Article, id=article_id, is_published=True)

    if not article.main_pdf or not article.main_pdf.file:
        raise Http404("PDF fayl topilmadi")

    # Increment download count
    article.increment_downloads()

    # Return file response
    return FileResponse(
        article.main_pdf.file.open('rb'),
        as_attachment=True,
        filename=f"{article.title}.pdf"
    )


def featured_articles(request):
    """Display featured articles"""
    articles = Article.objects.filter(
        is_published=True,
        featured=True
    ).select_related('issue__journal').prefetch_related('authors').order_by('-date_published')

    # Pagination
    paginator = Paginator(articles, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'articles': page_obj,
        'page_title': 'Tanlab Olingan Maqolalar - Imfaktor',
        'meta_description': 'Imfaktor portalidagi eng muhim va sifatli ilmiy maqolalar',
    }

    return render(request, 'articles_list.html', context)


def open_access_articles(request):
    """Display open access articles"""
    articles = Article.objects.filter(
        is_published=True,
        open_access=True
    ).select_related('issue__journal').prefetch_related('authors').order_by('-date_published')

    # Pagination
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'articles': page_obj,
        'page_title': 'Ochiq Kirish Maqolalari - Imfaktor',
        'meta_description': 'Imfaktor portalidagi ochiq kirish (Open Access) maqolalari',
    }

    return render(request, 'articles_list.html', context)


def latest_articles(request):
    """Display latest articles"""
    articles = Article.objects.filter(
        is_published=True
    ).select_related('issue__journal').prefetch_related('authors').order_by('-date_published')

    # Pagination
    paginator = Paginator(articles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'articles': page_obj,
        'page_title': 'So\'nggi Maqolalar - Imfaktor',
        'meta_description': 'Imfaktor portalidagi eng so\'nggi nashr etilgan ilmiy maqolalar',
    }

    return render(request, 'articles_list.html', context)


def articles_by_year(request, year):
    """Display articles by year"""
    try:
        year = int(year)
    except ValueError:
        raise Http404("Noto'g'ri yil")

    articles = Article.objects.filter(
        is_published=True,
        date_published__year=year
    ).select_related('issue__journal').prefetch_related('authors').order_by('-date_published')

    if not articles.exists():
        raise Http404(f"{year} yilda nashr etilgan maqolalar topilmadi")

    # Pagination
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'articles': page_obj,
        'year': year,
        'page_title': f'{year} Yil Maqolalari - Imfaktor',
        'meta_description': f'{year} yilda Imfaktor portalida nashr etilgan ilmiy maqolalar',
    }

    return render(request, 'articles_list.html', context)
