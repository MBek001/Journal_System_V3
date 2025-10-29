import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.core.exceptions import ValidationError
import logging
import os

from .config import ADMIN_USERNAME, ADMIN_PASSWORD

logger = logging.getLogger(__name__)

from .models import *


def check_admin_credentials(username, password):
    """Check admin credentials against config"""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def admin_login(request):
    """Handle admin login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if check_admin_credentials(username, password):
            request.session['is_admin'] = True
            request.session['admin_username'] = username
            request.session.set_expiry(int(os.getenv('SESSION_EXPIRY', 3600)))
            next_url = request.GET.get('next', '/admin/')
            return redirect(next_url)
        else:
            messages.error(request, "Noto'g'ri login yoki parol!")

    return render(request, 'login.html')


def admin_logout(request):
    """Handle admin logout"""
    request.session.flush()
    messages.success(request, "Tizimdan chiqdingiz!")
    return redirect('admin_login')


def require_admin_login(view_func):
    """Decorator to require admin login"""

    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect(f'/admin/login/?next={request.path}')
        return view_func(request, *args, **kwargs)

    return wrapper


def _create_or_update_author(first_name, last_name, middle_name, affiliation, email, orcid):
    """
    Helper function to create or update author by email.
    Only updates fields if new value is provided and different.
    """
    if not first_name or not last_name:
        raise ValidationError("Muallifning ismi va familiyasi majburiy.")

    author = None
    updated = False

    if email:
        try:
            author = Author.objects.get(email=email)
            # Only update fields if new data is provided and different
            if first_name and author.first_name != first_name:
                author.first_name = first_name
                updated = True
            if last_name and author.last_name != last_name:
                author.last_name = last_name
                updated = True
            if middle_name and author.middle_name != middle_name:
                author.middle_name = middle_name
                updated = True
            if affiliation and author.affiliation != affiliation:
                author.affiliation = affiliation
                updated = True
            if orcid and author.orcid != orcid:
                author.orcid = orcid
                updated = True
            if updated:
                author.save()
        except Author.DoesNotExist:
            pass

    if not author:
        # If email not given, generate a fake one to satisfy unique constraint
        email = email or f"{slugify(first_name)}.{slugify(last_name)}@example.com"
        author = Author.objects.create(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            affiliation=affiliation,
            orcid=orcid,
            is_active=True
        )
    return author


def _get_base_stats():
    """Helper function to get base dashboard statistics"""
    return {
        'total_articles': Article.objects.count(),
        'total_authors': Author.objects.count(),
        'total_journals': Journal.objects.count(),
        'total_issues': Issue.objects.count(),
        'total_views': sum(article.views for article in Article.objects.all()),
        'total_downloads': sum(article.downloads for article in Article.objects.all()),
    }


# MAIN DASHBOARD
@require_admin_login
def admin_dashboard(request):
    """Main admin dashboard"""
    try:
        stats = _get_base_stats()

        recent_articles = Article.objects.select_related('issue__journal').prefetch_related('authors').order_by(
            '-date_published')[:5]
        journals = Journal.objects.filter(is_active=True).annotate(article_count=Count('issues__articles'))

        # Ensure at least one journal exists
        if not journals.exists():
            Journal.objects.create(
                title="Umumiy Jurnal",
                url_slug="umumiy-jurnal",
                description="Standart jurnal",
                contact_email="info@imfaktor.uz",
                is_active=True
            )
            journals = Journal.objects.filter(is_active=True)

        # Additional data
        fan_tarmoq_list = FanTarmoq.objects.filter(is_active=True)
        ilmiy_nashr_list = IlmiyNashr.objects.filter(is_active=True)
        indexed_pages = Article.objects.filter(is_published=True).count() + Journal.objects.filter(
            is_active=True).count()
        scholar_articles = Article.objects.filter(doi__isnull=False).exclude(doi='').count()

        context = {
            **stats,
            'recent_articles': recent_articles,
            'journals': journals,
            'indexed_pages': indexed_pages,
            'scholar_articles': scholar_articles,
            'admin_username': request.session.get('admin_username', 'Admin'),
            'fan_tarmoq_list': fan_tarmoq_list,
            'ilmiy_nashr_list': ilmiy_nashr_list,
        }

        return render(request, 'admin.html', context)

    except Exception as e:
        logger.error(f"Error in admin_dashboard: {e}")
        messages.error(request, f'Dashboard yuklashda xatolik: {str(e)}')
        return render(request, 'admin.html', {'admin_username': request.session.get('admin_username', 'Admin')})


# JOURNAL MANAGEMENT
@require_admin_login
def journal_management_page(request, journal_id):
    """Individual journal management page"""
    try:
        journal = get_object_or_404(Journal, id=journal_id)

        # Get journal statistics
        total_articles = Article.objects.filter(issue__journal=journal).count()
        total_issues = Issue.objects.filter(journal=journal).count()
        total_views = sum(article.views for article in Article.objects.filter(issue__journal=journal))
        total_downloads = sum(article.downloads for article in Article.objects.filter(issue__journal=journal))

        context = {
            'journal': journal,
            'total_articles': total_articles,
            'total_issues': total_issues,
            'total_views': total_views,
            'total_downloads': total_downloads,
            'admin_username': request.session.get('admin_username', 'Admin'),
            'current_year': timezone.now().year,
        }

        return render(request, 'admin_journal.html', context)

    except Exception as e:
        logger.error(f"Error in journal_management_page: {e}")
        messages.error(request, f'Sahifa yuklashda xatolik: {str(e)}')
        return redirect('admin_dashboard')


@require_admin_login
def journal_issues_ajax(request, journal_id):
    """Get issues for specific journal"""
    try:
        page = int(request.GET.get('page', 1))
        journal = get_object_or_404(Journal, id=journal_id)

        issues = Issue.objects.filter(journal=journal).annotate(
            article_count=Count('articles')
        ).order_by('-year', '-volume', '-number')

        paginator = Paginator(issues, 20)
        page_obj = paginator.get_page(page)

        issues_data = []
        for issue in page_obj:
            issues_data.append({
                'id': issue.id,
                'volume': issue.volume,
                'number': issue.number,
                'year': issue.year,
                'title': issue.title or '',
                'date_published': issue.date_published.strftime('%d.%m.%Y') if issue.date_published else '',
                'is_published': issue.is_published,
                'article_count': issue.article_count,
                'has_cover': bool(issue.cover_image),
                'is_active': issue.is_active,
            })

        return JsonResponse({
            'success': True,
            'issues': issues_data,
            'pagination': {
                'current': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def journal_articles_ajax(request, journal_id):
    """Get articles for specific journal"""
    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')
        issue_filter = request.GET.get('issue', '')
        status_filter = request.GET.get('status', '')

        journal = get_object_or_404(Journal, id=journal_id)
        articles = Article.objects.filter(issue__journal=journal).select_related('issue').prefetch_related('authors')

        if search:
            articles = articles.filter(
                Q(title__icontains=search) |
                Q(keywords__icontains=search) |
                Q(abstract__icontains=search)
            )

        if issue_filter:
            articles = articles.filter(issue_id=issue_filter)

        if status_filter:
            if status_filter == 'published':
                articles = articles.filter(is_published=True)
            elif status_filter == 'draft':
                articles = articles.filter(is_published=False)
            elif status_filter == 'featured':
                articles = articles.filter(featured=True)

        articles = articles.order_by('-date_published', '-id')

        paginator = Paginator(articles, 20)
        page_obj = paginator.get_page(page)

        articles_data = []
        for article in page_obj:
            authors_list = [f"{author.first_name} {author.last_name}" for author in article.authors.all()]

            articles_data.append({
                'id': article.id,
                'title': article.title,
                'subtitle': getattr(article, 'subtitle', '') or '',
                'authors': authors_list,
                'issue_info': f"Vol.{article.issue.volume} No.{article.issue.number}" if article.issue else 'N/A',
                'date_published': article.date_published.strftime('%d.%m.%Y'),
                'views': getattr(article, 'views', 0),
                'is_published': article.is_published,
                'featured': getattr(article, 'featured', False),
            })

        return JsonResponse({
            'success': True,
            'articles': articles_data,
            'pagination': {
                'current': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_add_issue_ajax(request, journal_id):
    """Add issue to specific journal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal = get_object_or_404(Journal, id=journal_id)
        volume = request.POST.get('volume')
        number = request.POST.get('number')
        year = request.POST.get('year')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        date_published = request.POST.get('date_published')
        is_published = request.POST.get('is_published') == 'on'

        if not all([volume, number, year]):
            return JsonResponse({'success': False, 'error': "Majburiy maydonlar to'ldirilmagan"})

        if Issue.objects.filter(journal=journal, volume=volume, number=number, year=year).exists():
            return JsonResponse({'success': False, 'error': "Bu son allaqachon mavjud"})

        cover_image = request.FILES.get('cover_image')
        Issue.objects.filter(journal=journal, is_active=True).update(is_active=False)
        issue = Issue.objects.create(
            journal=journal,
            volume=int(volume),
            number=int(number),
            year=int(year),
            title=title,
            description=description,
            date_published=date_published if date_published else timezone.now().date(),
            is_published=is_published,
            cover_image=cover_image,
            is_active=True,
        )

        return JsonResponse({
            'success': True,
            'message': "Son muvaffaqiyatli qo'shildi",
            'issue_id': issue.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_settings_ajax(request, journal_id):
    """Update journal settings"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal = get_object_or_404(Journal, id=journal_id)

        journal.title = request.POST.get('title', journal.title)
        journal.initials = request.POST.get('initials', journal.initials)
        journal.url_slug = request.POST.get('url_slug', journal.url_slug)
        journal.abbreviation = request.POST.get('abbreviation', journal.abbreviation)
        journal.description = request.POST.get('description', journal.description)
        journal.meta_description = request.POST.get('meta_description', journal.meta_description)
        journal.contact_email = request.POST.get('contact_email', journal.contact_email)
        journal.website = request.POST.get('website', journal.website)
        journal.publisher = request.POST.get('publisher', journal.publisher)
        journal.issn_print = request.POST.get('issn_print', journal.issn_print)
        journal.issn_online = request.POST.get('issn_online', journal.issn_online)
        journal.is_active = request.POST.get('is_active') == 'on'
        journal.is_open_access = request.POST.get('is_open_access') == 'on'

        if 'cover_image' in request.FILES:
            if journal.cover_image:
                try:
                    journal.cover_image.delete()
                except:
                    pass
            journal.cover_image = request.FILES['cover_image']

        journal.save()

        return JsonResponse({
            'success': True,
            'message': "Jurnal sozlamalari saqlandi"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# JOURNAL CRUD OPERATIONS
@require_admin_login
@csrf_protect
@transaction.atomic
def add_journal_ajax(request):
    """Add new journal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        title = request.POST.get('title')
        initials = request.POST.get('initials', '')
        abbreviation = request.POST.get('abbreviation', '')
        url_slug = request.POST.get('url_slug')
        description = request.POST.get('description', '')
        meta_description = request.POST.get('meta_description', '')
        contact_email = request.POST.get('contact_email', '')
        website = request.POST.get('website', '')
        publisher = request.POST.get('publisher', '')
        issn_print = request.POST.get('issn_print', '')
        issn_online = request.POST.get('issn_online', '')
        is_active = request.POST.get('is_active') == 'on'
        is_open_access = request.POST.get('is_open_access') == 'on'

        if not title:
            return JsonResponse({'success': False, 'error': "Jurnal nomi majburiy"})

        if not url_slug:
            url_slug = slugify(title)
        if Journal.objects.filter(url_slug=url_slug).exists():
            return JsonResponse({'success': False, 'error': "Bu URL slug allaqachon mavjud"})

        cover_image = request.FILES.get('cover_image')
        journal = Journal.objects.create(
            title=title,
            initials=initials,
            abbreviation=abbreviation,
            url_slug=url_slug,
            description=description,
            meta_description=meta_description,
            contact_email=contact_email or 'info@imfaktor.uz',
            website=website,
            publisher=publisher,
            issn_print=issn_print,
            issn_online=issn_online,
            is_active=is_active,
            is_open_access=is_open_access,
            cover_image=cover_image
        )

        return JsonResponse({
            'success': True,
            'message': "Jurnal muvaffaqiyatli qo'shildi",
            'journal_id': journal.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def journals_list_ajax(request):
    """Get list of journals for AJAX requests"""
    try:
        journals = Journal.objects.annotate(
            article_count=Count('issues__articles', distinct=True),
            issue_count=Count('issues', distinct=True)
        ).order_by('-is_active', 'title')

        journals_data = []
        for journal in journals:
            journals_data.append({
                'id': journal.id,
                'title': journal.title,
                'url_slug': journal.url_slug,
                'initials': journal.initials or '',
                'description': journal.description or '',
                'issn_print': journal.issn_print or '',
                'issn_online': journal.issn_online or '',
                'website': journal.website or '',
                'publisher': journal.publisher or '',
                'is_active': journal.is_active,
                'is_open_access': journal.is_open_access,
                'article_count': journal.article_count,
                'issue_count': journal.issue_count,
                'created_at': journal.created_at.strftime('%d.%m.%Y') if hasattr(journal, 'created_at') else ''
            })

        return JsonResponse({'success': True, 'journals': journals_data})

    except Exception as e:
        logger.error(f"Error in journals_list_ajax: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def update_journal_ajax(request, journal_id):
    """Update journal via AJAX"""
    if request.method == 'POST':
        try:
            journal = get_object_or_404(Journal, id=journal_id)
            journal.title = request.POST.get('title', journal.title)
            journal.initials = request.POST.get('initials', journal.initials)
            journal.abbreviation = request.POST.get('abbreviation', journal.abbreviation)
            journal.description = request.POST.get('description', journal.description)
            journal.meta_description = request.POST.get('meta_description', journal.meta_description)
            journal.contact_email = request.POST.get('contact_email', journal.contact_email)
            journal.website = request.POST.get('website', journal.website)
            journal.publisher = request.POST.get('publisher', journal.publisher)
            journal.issn_print = request.POST.get('issn_print', journal.issn_print)
            journal.issn_online = request.POST.get('issn_online', journal.issn_online)
            journal.is_active = request.POST.get('is_active') == 'on'
            journal.is_open_access = request.POST.get('is_open_access') == 'on'

            if 'cover_image' in request.FILES:
                if journal.cover_image:
                    try:
                        journal.cover_image.delete()
                    except:
                        pass
                journal.cover_image = request.FILES['cover_image']

            journal.save()
            return JsonResponse({'success': True, 'message': "Jurnal yangilandi"})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            journal = get_object_or_404(Journal, id=journal_id)
            journal_data = {
                'id': journal.id,
                'title': journal.title,
                'initials': journal.initials or '',
                'abbreviation': journal.abbreviation or '',
                'url_slug': journal.url_slug,
                'description': journal.description or '',
                'meta_description': journal.meta_description or '',
                'contact_email': journal.contact_email or '',
                'website': journal.website or '',
                'publisher': journal.publisher or '',
                'issn_print': journal.issn_print or '',
                'issn_online': journal.issn_online or '',
                'is_active': journal.is_active,
                'is_open_access': journal.is_open_access,
                'has_cover': bool(journal.cover_image)
            }
            return JsonResponse({'success': True, 'journal': journal_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_journal_ajax(request, journal_id):
    """Delete journal via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal = get_object_or_404(Journal, id=journal_id)
        article_count = Article.objects.filter(issue__journal=journal).count()
        if article_count > 0:
            return JsonResponse({
                'success': False,
                'error': f"Bu jurnalda {article_count} ta maqola mavjud. Avval maqolalarni o'chiring yoki boshqa jurnalga ko'chiring."
            })

        if journal.cover_image:
            try:
                journal.cover_image.delete()
            except:
                pass

        journal.delete()
        return JsonResponse({'success': True, 'message': "Jurnal o'chirildi"})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ISSUES CRUD OPERATIONS
@require_admin_login
@csrf_protect
@transaction.atomic
def add_issue_ajax(request):
    """Add new issue via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal_id = request.POST.get('journal')
        volume = request.POST.get('volume')
        number = request.POST.get('number')
        year = request.POST.get('year')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        date_published = request.POST.get('date_published')
        is_published = request.POST.get('is_published') == 'on'

        if not all([journal_id, volume, number, year]):
            return JsonResponse({'success': False, 'error': "Majburiy maydonlar to'ldirilmagan"})

        journal = get_object_or_404(Journal, id=journal_id)
        if Issue.objects.filter(journal=journal, volume=volume, number=number, year=year).exists():
            return JsonResponse({'success': False, 'error': "Bu son allaqachon mavjud"})

        Issue.objects.filter(journal=journal, is_active=True).update(is_active=False)
        print("changeeeed")

        cover_image = request.FILES.get('cover_image')
        issue = Issue.objects.create(
            journal=journal,
            volume=int(volume),
            number=int(number),
            year=int(year),
            title=title,
            description=description,
            date_published=date_published if date_published else timezone.now().date(),
            is_published=is_published,
            cover_image=cover_image,
            is_active=True,
        )

        return JsonResponse({
            'success': True,
            'message': "Son muvaffaqiyatli qo'shildi",
            'issue_id': issue.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def issues_list_ajax(request):
    """Get list of issues for AJAX requests"""
    try:
        journal_id = request.GET.get('journal')
        issues = Issue.objects.select_related('journal').annotate(
            article_count=Count('articles')
        )

        if journal_id:
            issues = issues.filter(journal_id=journal_id)

        issues = issues.order_by('-year', '-volume', '-number')
        issues_data = []
        for issue in issues:
            issues_data.append({
                'id': issue.id,
                'journal_title': issue.journal.title,
                'journal_id': issue.journal.id,
                'journal_slug': issue.journal.url_slug,
                'volume': issue.volume,
                'number': issue.number,
                'year': issue.year,
                'title': issue.title or '',
                'date_published': issue.date_published.strftime('%d.%m.%Y') if issue.date_published else '',
                'is_published': issue.is_published,
                'article_count': issue.article_count,
                'is_active': issue.is_active,
                'full_citation': f"Jild {issue.volume}, Son {issue.number} ({issue.year})"
            })

        return JsonResponse({'success': True, 'issues': issues_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_article_ajax(request, article_id):
    """Delete article via AJAX"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        article = get_object_or_404(Article, id=article_id)
        article_title = article.title

        # Delete associated files
        if article.main_pdf:
            try:
                if article.main_pdf.file:
                    article.main_pdf.file.delete()
                article.main_pdf.delete()
            except:
                pass

        # Delete supplementary files if they exist
        try:
            for file in article.supplementary_files.all():
                try:
                    if file.file:
                        file.file.delete()
                    file.delete()
                except:
                    pass
        except:
            pass

        # Delete article-author relationships
        ArticleAuthor.objects.filter(article=article).delete()

        # Delete the article
        article.delete()

        logger.info(f"Article '{article_title}' deleted successfully")

        return JsonResponse({
            'success': True,
            'message': "Maqola muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


# ISSUES CRUD OPERATIONS
@require_admin_login
@csrf_protect
@transaction.atomic
def update_issue_ajax(request, issue_id):
    """Update issue via AJAX"""

    if request.method == 'POST':
        try:
            issue = get_object_or_404(Issue, id=issue_id)
            issue.volume = int(request.POST.get('volume', issue.volume))
            issue.number = int(request.POST.get('number', issue.number))
            issue.year = int(request.POST.get('year', issue.year))
            issue.title = request.POST.get('title', issue.title)
            issue.description = request.POST.get('description', issue.description)
            issue.is_published = request.POST.get('is_published') == 'on'

            date_published = request.POST.get('date_published')
            if date_published:
                issue.date_published = date_published

            if 'cover_image' in request.FILES:
                if issue.cover_image:
                    try:
                        issue.cover_image.delete()
                    except Exception as e:
                        pass  # optionally log this
                issue.cover_image = request.FILES['cover_image']

            issue.save()
            return JsonResponse({'success': True, 'message': "Son yangilandi"})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            issue = get_object_or_404(Issue, id=issue_id)

            issue_data = {
                'id': issue.id,
                'journal_id': issue.journal.id if issue.journal else None,
                'journal_slug': issue.journal.url_slug if issue.journal else '',
                'volume': issue.volume,
                'number': issue.number,
                'year': issue.year,
                'title': issue.title,
                'description': issue.description,
                'date_published': issue.date_published.strftime('%Y-%m-%d') if issue.date_published else '',
                'is_published': issue.is_published,
                'has_cover': bool(issue.cover_image),
            }

            return JsonResponse({'success': True, 'issue': issue_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov turi"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_issue_ajax(request, issue_id):
    """Delete issue via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        issue = get_object_or_404(Issue, id=issue_id)
        article_count = Article.objects.filter(issue=issue).count()
        if article_count > 0:
            return JsonResponse({
                'success': False,
                'error': f"Bu sonda {article_count} ta maqola mavjud. Avval maqolalarni o'chiring."
            })

        if issue.cover_image:
            try:
                issue.cover_image.delete()
            except:
                pass

        issue.delete()
        return JsonResponse({'success': True, 'message': "Son o'chirildi"})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# AUTHORS CRUD OPERATIONS
@require_admin_login
def authors_list_ajax(request):
    """Get paginated list of authors for AJAX requests"""
    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '')

        authors = Author.objects.annotate(article_count=Count('articleauthor'))

        if search:
            authors = authors.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(affiliation__icontains=search) |
                Q(orcid__icontains=search)
            )

        authors = authors.order_by('last_name', 'first_name')
        paginator = Paginator(authors, 20)
        page_obj = paginator.get_page(page)

        authors_data = []
        for author in page_obj:
            authors_data.append({
                'id': author.id,
                'full_name': author.full_name,
                'first_name': author.first_name,
                'middle_name': author.middle_name or '',
                'last_name': author.last_name,
                'email': author.email or '',
                'affiliation': author.affiliation or '',
                'academic_title': author.academic_title or '',
                'academic_degree': author.academic_degree or '',
                'orcid': author.orcid or '',
                'google_scholar_id': author.google_scholar_id or '',
                'article_count': author.article_count,
                'is_active': author.is_active
            })

        return JsonResponse({
            'success': True,
            'authors': authors_data,
            'pagination': {
                'current': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_count': paginator.count
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def add_author_ajax(request):
    """Add new author via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        email = request.POST.get('email', '').strip()
        affiliation = request.POST.get('affiliation', '').strip()
        department = request.POST.get('department', '').strip()
        position = request.POST.get('position', '').strip()
        academic_title = request.POST.get('academic_title', '').strip()
        academic_degree = request.POST.get('academic_degree', '').strip()
        orcid = request.POST.get('orcid', '').strip()
        google_scholar_id = request.POST.get('google_scholar_id', '').strip()
        website = request.POST.get('website', '').strip()
        bio = request.POST.get('bio', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validate required fields
        if not first_name or not last_name:
            return JsonResponse({'success': False, 'error': "Ism va familiya majburiy"})

        # Check if email already exists
        if email and Author.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': "Bu email allaqachon mavjud"})

        # Create author
        author = Author.objects.create(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email or f"{slugify(first_name)}.{slugify(last_name)}@example.com",
            affiliation=affiliation,
            department=department,
            position=position,
            academic_title=academic_title,
            academic_degree=academic_degree,
            orcid=orcid,
            google_scholar_id=google_scholar_id,
            website=website,
            bio=bio,
            is_active=is_active
        )

        # Handle photo upload
        if 'photo' in request.FILES:
            author.photo = request.FILES['photo']
            author.save()

        logger.info(f"Author {author.full_name} created successfully")

        return JsonResponse({
            'success': True,
            'message': "Muallif muvaffaqiyatli qo'shildi",
            'author_id': author.id
        })

    except Exception as e:
        logger.error(f"Error adding author: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
@csrf_protect
@transaction.atomic
def update_author_ajax(request, author_id):
    """Update author via AJAX"""
    if request.method == 'POST':
        try:
            author = get_object_or_404(Author, id=author_id)
            author.first_name = request.POST.get('first_name', author.first_name)
            author.middle_name = request.POST.get('middle_name', author.middle_name)
            author.last_name = request.POST.get('last_name', author.last_name)
            author.email = request.POST.get('email', author.email)
            author.affiliation = request.POST.get('affiliation', author.affiliation)
            author.department = request.POST.get('department', author.department)
            author.position = request.POST.get('position', author.position)
            author.academic_title = request.POST.get('academic_title', author.academic_title)
            author.academic_degree = request.POST.get('academic_degree', author.academic_degree)
            author.orcid = request.POST.get('orcid', author.orcid)
            author.google_scholar_id = request.POST.get('google_scholar_id', author.google_scholar_id)
            author.website = request.POST.get('website', author.website)
            author.bio = request.POST.get('bio', author.bio)
            author.is_active = request.POST.get('is_active') == 'on'

            if 'photo' in request.FILES:
                if author.photo:
                    try:
                        author.photo.delete()
                    except:
                        pass
                author.photo = request.FILES['photo']

            author.save()
            return JsonResponse({'success': True, 'message': "Muallif ma'lumotlari yangilandi"})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            author = get_object_or_404(Author, id=author_id)
            author_data = {
                'id': author.id,
                'first_name': author.first_name,
                'middle_name': author.middle_name or '',
                'last_name': author.last_name,
                'email': author.email,
                'affiliation': author.affiliation,
                'department': author.department,
                'position': author.position,
                'orcid': author.orcid,
                'google_scholar_id': author.google_scholar_id,
                'website': author.website,
                'bio': author.bio,
                'is_active': author.is_active,
                'has_photo': bool(author.photo)
            }
            return JsonResponse({'success': True, 'author': author_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_author_ajax(request, author_id):
    """Delete author via AJAX"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        author = get_object_or_404(Author, id=author_id)

        # Check if author has articles
        article_count = ArticleAuthor.objects.filter(author=author).count()
        if article_count > 0:
            return JsonResponse({
                'success': False,
                'error': f"Bu muallifning {article_count} ta maqolasi mavjud. Avval maqolalarni boshqa muallifga o'tkazing."
            })

        author_name = author.full_name

        # Delete photo if exists
        if author.photo:
            try:
                author.photo.delete()
            except:
                pass

        # Delete the author
        author.delete()

        logger.info(f"Author '{author_name}' deleted successfully")

        return JsonResponse({
            'success': True,
            'message': "Muallif muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting author {author_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
def author_details_ajax(request, author_id):
    """Get author details for viewing"""
    try:
        author = get_object_or_404(Author, id=author_id)
        articles = Article.objects.filter(
            articleauthor__author=author
        ).select_related('issue__journal').order_by('-date_published')[:10]

        author_data = {
            'id': author.id,
            'full_name': author.full_name,
            'first_name': author.first_name,
            'middle_name': author.middle_name or '',
            'last_name': author.last_name,
            'email': author.email,
            'affiliation': author.affiliation or '',
            'department': author.department or '',
            'position': author.position or '',
            'academic_title': author.academic_title or '',
            'academic_degree': author.academic_degree or '',
            'orcid': author.orcid or '',
            'google_scholar_id': author.google_scholar_id or '',
            'website': author.website or '',
            'bio': author.bio or '',
            'is_active': author.is_active,
            'has_photo': bool(author.photo),
            'photo_url': author.photo.url if author.photo else None,
            'article_count': articles.count(),
            'recent_articles': [
                {
                    'id': article.id,
                    'title': article.title,
                    'journal': article.issue.journal.title if article.issue else 'N/A',
                    'date': article.date_published.strftime('%d.%m.%Y'),
                    'slug': article.slug
                }
                for article in articles
            ]
        }

        return JsonResponse({'success': True, 'author': author_data})

    except Exception as e:
        logger.error(f"Error getting author details: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# UTILITY FUNCTIONS
@require_admin_login
def get_journal_issues(request, journal_id):
    """Get issues for a specific journal"""
    try:
        issues = Issue.objects.filter(
            journal_id=journal_id,
            is_published=True
        ).order_by('-year', '-volume', '-number')

        issues_data = []
        for issue in issues:
            issues_data.append({
                'id': issue.id,
                'volume': issue.volume,
                'number': issue.number,
                'year': issue.year,
                'title': issue.title,
                'full_citation': f"Jild {issue.volume}, Son {issue.number} ({issue.year})",
                'is_published': issue.is_published
            })

        return JsonResponse({'success': True, 'issues': issues_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# SEO MANAGEMENT

@require_admin_login
def get_seo_status(request):
    """Get SEO status and statistics"""
    try:
        seo = SiteSEO.objects.first()

        # Get counts
        published_articles = Article.objects.filter(is_published=True).count()
        active_journals = Journal.objects.filter(is_active=True).count()
        active_authors = Author.objects.filter(is_active=True).count()
        published_issues = Issue.objects.filter(is_published=True).count()

        return JsonResponse({
            'success': True,
            'seo_enabled': bool(seo and seo.enable_google_scholar),
            'auto_sitemap': bool(seo and seo.auto_sitemap),
            'stats': {
                'articles': published_articles,
                'journals': active_journals,
                'authors': active_authors,
                'issues': published_issues
            },
            'urls': {
                'sitemap': request.build_absolute_uri('/sitemap.xml'),
                'robots': request.build_absolute_uri('/robots.txt')
            }
        })

    except Exception as e:
        logger.error(f"Error getting SEO status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def load_seo(request):
    """Load SEO settings"""
    try:
        seo = SiteSEO.objects.first()
        # build a dict even if seo==None
        seo_data = {
            'meta_title': seo.meta_title if seo else '',
            'meta_description': seo.meta_description if seo else '',
            'meta_keywords': seo.meta_keywords if seo else '',
            'publisher_name': seo.publisher_name if seo else '',
            'enable_google_scholar': bool(seo and seo.enable_google_scholar),
            'auto_sitemap': bool(seo and seo.auto_sitemap),
        }

        stats = {
            'articles': Article.objects.filter(is_published=True).count(),
            'journals': Journal.objects.filter(is_active=True).count(),
            'authors': Author.objects.filter(is_active=True).count(),
            'issues': Issue.objects.filter(is_published=True).count(),
        }

        urls = {
            'sitemap': request.build_absolute_uri('/sitemap.xml'),
            'robots': request.build_absolute_uri('/robots.txt'),
        }

        return JsonResponse({
            'success': True,
            'seo': seo_data,
            'stats': stats,
            'urls': urls,
        })

    except Exception as e:
        logger.error(f"Error getting SEO status: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
def save_seo_settings(request):
    """Save SEO settings"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Invalid request method"})

    try:
        form_data = request.POST
        seo, created = SiteSEO.objects.update_or_create(
            id=1,  # Single SEO config
            defaults={
                'meta_title': form_data.get('site_title'),
                'meta_description': form_data.get('site_description'),
                'meta_keywords': form_data.get('site_keywords'),
                'publisher_name': form_data.get('publisher_name'),
                'enable_google_scholar': 'enable_google_scholar' in form_data,
                'auto_sitemap': 'auto_sitemap' in form_data,
            }
        )
        return JsonResponse({'success': True, 'message': "SEO settings saved"})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# EXPORT FUNCTIONS
@require_admin_login
def export_articles_csv(request):
    """Export articles to CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="articles_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Subtitle', 'Authors', 'Journal', 'Issue',
        'Date Published', 'Keywords', 'Views', 'Downloads', 'DOI',
        'Language', 'Pages', 'Open Access', 'Featured'
    ])

    articles = Article.objects.select_related('issue__journal').prefetch_related('authors')
    for article in articles:
        authors = '; '.join([author.full_name for author in article.authors.all()])
        page_range = ''
        if article.first_page and article.last_page:
            page_range = f"{article.first_page}-{article.last_page}"
        elif article.first_page:
            page_range = str(article.first_page)

        writer.writerow([
            article.id,
            article.title,
            article.subtitle or '',
            authors,
            article.issue.journal.title if article.issue else 'N/A',
            f"Vol.{article.issue.volume} No.{article.issue.number}" if article.issue else 'N/A',
            article.date_published.strftime('%Y-%m-%d'),
            article.keywords or '',
            getattr(article, 'views', 0),
            getattr(article, 'downloads', 0),
            article.doi or '',
            getattr(article, 'language', 'uz'),
            page_range,
            'Yes' if getattr(article, 'open_access', False) else 'No',
            'Yes' if getattr(article, 'featured', False) else 'No'
        ])

    return response


@require_admin_login
def export_authors_csv(request):
    """Export authors to CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="authors_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Full Name', 'Email', 'Affiliation', 'Department', 'Position',
        'ORCID', 'Google Scholar ID', 'Website', 'Articles Count', 'Active'
    ])

    authors = Author.objects.annotate(article_count=Count('articleauthor'))
    for author in authors:
        writer.writerow([
            author.id,
            author.full_name,
            author.email or '',
            author.affiliation or '',
            author.department or '',
            author.position or '',
            author.orcid or '',
            author.google_scholar_id or '',
            author.website or '',
            author.article_count,
            'Yes' if author.is_active else 'No'
        ])

    return response


@require_admin_login
def export_journals_csv(request):
    """Export journals to CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="journals_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'URL Slug', 'ISSN Print', 'ISSN Online', 'Publisher',
        'Articles Count', 'Issues Count', 'Active', 'Open Access'
    ])

    journals = Journal.objects.annotate(
        article_count=Count('issues__articles', distinct=True),
        issue_count=Count('issues', distinct=True)
    )

    for journal in journals:
        writer.writerow([
            journal.id,
            journal.title,
            journal.url_slug,
            journal.issn_print or '',
            journal.issn_online or '',
            journal.publisher or '',
            journal.article_count,
            journal.issue_count,
            'Yes' if journal.is_active else 'No',
            'Yes' if journal.is_open_access else 'No'
        ])

    return response


# SITEMAP AND ROBOTS
def generate_sitemap(request):
    """Generate XML sitemap for SEO"""

    if request.method == "GET":
        # Handle GET request - return actual sitemap XML
        try:
            articles = Article.objects.filter(
                is_published=True,
                issue__isnull=False
            ).select_related('issue__journal').order_by('-date_published')

            journals = Journal.objects.filter(is_active=True)
            issues = Issue.objects.filter(is_published=True).select_related('journal')
            authors = Author.objects.filter(is_active=True)

            sitemap_content = render_to_string('sitemap.xml', {
                'articles': articles,
                'journals': journals,
                'issues': issues,
                'authors': authors,
                'domain': request.get_host(),
                'protocol': 'https' if request.is_secure() else 'http',
                'enable_google_scholar': SiteSEO.objects.first().enable_google_scholar if SiteSEO.objects.first() else False,
            })

            return HttpResponse(sitemap_content, content_type='application/xml')

        except Exception as e:
            logger.error(f"Error generating sitemap: {str(e)}")
            return HttpResponse("Error generating sitemap", status=500)

    elif request.method == "POST":
        # Handle POST request - update/refresh sitemap and return JSON
        try:
            articles = Article.objects.filter(
                is_published=True,
                issue__isnull=False
            ).select_related('issue__journal').order_by('-date_published')

            journals = Journal.objects.filter(is_active=True)
            issues = Issue.objects.filter(is_published=True).select_related('journal')
            authors = Author.objects.filter(is_active=True)

            # Generate and potentially cache the sitemap
            sitemap_content = render_to_string('sitemap.xml', {
                'articles': articles,
                'journals': journals,
                'issues': issues,
                'authors': authors,
                'domain': request.get_host(),
                'protocol': 'https' if request.is_secure() else 'http',
                'enable_google_scholar': SiteSEO.objects.first().enable_google_scholar if SiteSEO.objects.first() else False,
            })

            # You can save to file or cache here if needed
            # Example: save to static file
            # with open('static/sitemap.xml', 'w') as f:
            #     f.write(sitemap_content)

            return JsonResponse({
                'success': True,
                'message': 'Sitemap muvaffaqiyatli yangilandi!',
                'stats': {
                    'articles': articles.count(),
                    'journals': journals.count(),
                    'issues': issues.count(),
                    'authors': authors.count()
                }
            })

        except Exception as e:
            logger.error(f"Error updating sitemap: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': "Method not allowed"})


@require_admin_login
def update_sitemap_manual(request):
    """Manually trigger sitemap update"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Invalid request method"})

    try:
        # Generate sitemap content
        articles = Article.objects.filter(
            is_published=True,
            issue__isnull=False
        ).select_related('issue__journal').order_by('-date_published')

        journals = Journal.objects.filter(is_active=True)
        issues = Issue.objects.filter(is_published=True).select_related('journal')
        authors = Author.objects.filter(is_active=True)

        return JsonResponse({
            'success': True,
            'message': 'Sitemap muvaffaqiyatli yangilandi!',
            'stats': {
                'articles': articles.count(),
                'journals': journals.count(),
                'issues': issues.count(),
                'authors': authors.count()
            }
        })

    except Exception as e:
        logger.error(f"Error updating sitemap: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def robots_txt(request):
    """Generate robots.txt for SEO"""

    if request.method == "GET":
        # Handle GET request - return actual robots.txt content
        try:
            seo = SiteSEO.objects.first()

            lines = [
                "User-agent: *",
                "Allow: /",
                "",
                "# Sitemaps",
                f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
                "",
            ]

            if not (seo and seo.enable_google_scholar):
                lines.extend([
                    "# Google Scholar disabled - limited indexing",
                    "Disallow: /admin/",
                    "Disallow: /api/",
                ])
            else:
                lines.extend([
                    "# Disallow admin areas",
                    "Disallow: /admin/",
                    "Disallow: /api/",
                    "",
                    "# Allow important pages",
                    "Allow: /articles/",
                    "Allow: /journals/",
                    "Allow: /authors/",
                    "Allow: /issues/",
                ])

            robots_content = "\n".join(lines)
            return HttpResponse(robots_content, content_type='text/plain')

        except Exception as e:
            logger.error(f"Error generating robots.txt: {str(e)}")
            return HttpResponse("Error generating robots.txt", status=500)

    elif request.method == "POST":
        # Handle POST request - update robots.txt and return JSON
        try:
            seo = SiteSEO.objects.first()

            lines = [
                "User-agent: *",
                "Allow: /",
                "",
                "# Sitemaps",
                f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
                "",
            ]

            if not (seo and seo.enable_google_scholar):
                lines.extend([
                    "# Google Scholar disabled - limited indexing",
                    "Disallow: /admin/",
                    "Disallow: /api/",
                ])
            else:
                lines.extend([
                    "# Disallow admin areas",
                    "Disallow: /admin/",
                    "Disallow: /api/",
                    "",
                    "# Allow important pages",
                    "Allow: /articles/",
                    "Allow: /journals/",
                    "Allow: /authors/",
                    "Allow: /issues/",
                ])

            robots_content = "\n".join(lines)

            # You can save to file here if needed
            # with open('static/robots.txt', 'w') as f:
            #     f.write(robots_content)

            return JsonResponse({
                'success': True,
                'message': 'Robots.txt muvaffaqiyatli yangilandi!',
                'content_preview': robots_content[:200] + "..." if len(robots_content) > 200 else robots_content
            })

        except Exception as e:
            logger.error(f"Error updating robots.txt: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': "Method not allowed"})


@require_admin_login
def update_robots_manual(request):
    """Manually trigger robots.txt update"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Invalid request method"})

    try:
        seo = SiteSEO.objects.first()

        # Generate robots.txt content
        lines = [
            "User-agent: *",
            "Allow: /",
            "",
            "# Sitemaps",
            f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
            "",
        ]

        if not (seo and seo.enable_google_scholar):
            lines.extend([
                "# Google Scholar disabled - limited indexing",
                "Disallow: /admin/",
                "Disallow: /api/",
            ])
        else:
            lines.extend([
                "# Disallow admin areas",
                "Disallow: /admin/",
                "Disallow: /api/",
                "",
                "# Allow important pages",
                "Allow: /articles/",
                "Allow: /journals/",
                "Allow: /authors/",
                "Allow: /issues/",
            ])

        robots_content = "\n".join(lines)

        return JsonResponse({
            'success': True,
            'message': 'Robots.txt muvaffaqiyatli yangilandi!',
            'content_preview': robots_content[:200] + "..." if len(robots_content) > 200 else robots_content
        })

    except Exception as e:
        logger.error(f"Error updating robots.txt: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def get_seo_status(request):
    """Get SEO status and statistics"""
    try:
        seo = SiteSEO.objects.first()

        # Get counts
        published_articles = Article.objects.filter(is_published=True).count()
        active_journals = Journal.objects.filter(is_active=True).count()
        active_authors = Author.objects.filter(is_active=True).count()
        published_issues = Issue.objects.filter(is_published=True).count()

        return JsonResponse({
            'success': True,
            'seo_enabled': bool(seo and seo.enable_google_scholar),
            'auto_sitemap': bool(seo and seo.auto_sitemap),
            'stats': {
                'articles': published_articles,
                'journals': active_journals,
                'authors': active_authors,
                'issues': published_issues
            },
            'urls': {
                'sitemap': request.build_absolute_uri('/sitemap.xml'),
                'robots': request.build_absolute_uri('/robots.txt')
            }
        })

    except Exception as e:
        logger.error(f"Error getting SEO status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def add_fan_tarmoq_ajax(request):
    """Add FanTarmoq via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active', 'on') == 'on'

        if not name:
            return JsonResponse({'success': False, 'error': "Nom majburiy"})

        if FanTarmoq.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': "Bu nom allaqachon mavjud"})

        fan_tarmoq = FanTarmoq.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )

        return JsonResponse({
            'success': True,
            'message': "Fan tarmoq qo'shildi",
            'id': fan_tarmoq.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def fan_tarmoq_list_ajax(request):
    """Get list of FanTarmoq for AJAX requests"""
    try:
        fan_tarmoqs = FanTarmoq.objects.all().order_by('name')
        fan_tarmoqs_data = []
        for ft in fan_tarmoqs:
            fan_tarmoqs_data.append({
                'id': ft.id,
                'name': ft.name,
                'slug': ft.slug,
                'description': ft.description or '',
                'is_active': ft.is_active
            })
        return JsonResponse({'success': True, 'fan_tarmoqs': fan_tarmoqs_data})
    except Exception as e:
        logger.error(f"Error in fan_tarmoq_list_ajax: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def edit_fan_tarmoq_ajax(request, fan_tarmoq_id):
    """Edit FanTarmoq via AJAX"""
    if request.method == 'POST':
        try:
            fan_tarmoq = get_object_or_404(FanTarmoq, id=fan_tarmoq_id)
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active', 'on') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': "Nom majburiy"})

            # Check if another FanTarmoq with the same name exists (excluding current one)
            if FanTarmoq.objects.filter(name__iexact=name).exclude(id=fan_tarmoq_id).exists():
                return JsonResponse({'success': False, 'error': "Bu nom allaqachon mavjud"})

            fan_tarmoq.name = name
            fan_tarmoq.description = description
            fan_tarmoq.is_active = is_active
            fan_tarmoq.save()

            return JsonResponse({
                'success': True,
                'message': "Fan tarmoq muvaffaqiyatli yangilandi"
            })

        except Exception as e:
            logger.error(f"Error editing FanTarmoq {fan_tarmoq_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        # This endpoint can be used to pre-fill the edit modal
        try:
            fan_tarmoq = get_object_or_404(FanTarmoq, id=fan_tarmoq_id)
            fan_tarmoq_data = {
                'id': fan_tarmoq.id,
                'name': fan_tarmoq.name,
                'description': fan_tarmoq.description or '',
                'is_active': fan_tarmoq.is_active
            }
            return JsonResponse({'success': True, 'fan_tarmoq': fan_tarmoq_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov turi"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_fan_tarmoq_ajax(request, fan_tarmoq_id):
    """Delete FanTarmoq via AJAX"""
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        fan_tarmoq = get_object_or_404(FanTarmoq, id=fan_tarmoq_id)
        fan_tarmoq_name = fan_tarmoq.name

        fan_tarmoq.delete()

        logger.info(f"FanTarmoq '{fan_tarmoq_name}' deleted successfully")
        return JsonResponse({
            'success': True,
            'message': "Fan tarmoq muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting FanTarmoq {fan_tarmoq_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def add_ilmiy_nashr_ajax(request):
    """Add IlmiyNashr via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active', 'on') == 'on'

        if not name:
            return JsonResponse({'success': False, 'error': "Nom majburiy"})

        if IlmiyNashr.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': "Bu nom allaqachon mavjud"})

        ilmiy_nashr = IlmiyNashr.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )

        return JsonResponse({
            'success': True,
            'message': "Ilmiy nashr turi qo'shildi",
            'id': ilmiy_nashr.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def ilmiy_nashr_list_ajax(request):
    """Get list of IlmiyNashr for AJAX requests"""
    try:
        ilmiy_nashrs = IlmiyNashr.objects.all().order_by('name')
        ilmiy_nashrs_data = []
        for in_item in ilmiy_nashrs:
            ilmiy_nashrs_data.append({
                'id': in_item.id,
                'name': in_item.name,
                'slug': in_item.slug,
                'description': in_item.description or '',
                'is_active': in_item.is_active
            })
        return JsonResponse({'success': True, 'ilmiy_nashrs': ilmiy_nashrs_data})
    except Exception as e:
        logger.error(f"Error in ilmiy_nashr_list_ajax: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def edit_ilmiy_nashr_ajax(request, ilmiy_nashr_id):
    """Edit IlmiyNashr via AJAX"""
    if request.method == 'POST':
        try:
            ilmiy_nashr = get_object_or_404(IlmiyNashr, id=ilmiy_nashr_id)
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active', 'on') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': "Nom majburiy"})
            if IlmiyNashr.objects.filter(name__iexact=name).exclude(id=ilmiy_nashr_id).exists():
                return JsonResponse({'success': False, 'error': "Bu nom allaqachon mavjud"})

            ilmiy_nashr.name = name
            ilmiy_nashr.description = description
            ilmiy_nashr.is_active = is_active
            ilmiy_nashr.save()

            return JsonResponse({
                'success': True,
                'message': "Ilmiy nashr turi muvaffaqiyatli yangilandi"
            })

        except Exception as e:
            logger.error(f"Error editing IlmiyNashr {ilmiy_nashr_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        # This endpoint can be used to pre-fill the edit modal
        try:
            ilmiy_nashr = get_object_or_404(IlmiyNashr, id=ilmiy_nashr_id)
            ilmiy_nashr_data = {
                'id': ilmiy_nashr.id,
                'name': ilmiy_nashr.name,
                'description': ilmiy_nashr.description or '',
                'is_active': ilmiy_nashr.is_active
            }
            return JsonResponse({'success': True, 'ilmiy_nashr': ilmiy_nashr_data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov turi"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_ilmiy_nashr_ajax(request, ilmiy_nashr_id):
    """Delete IlmiyNashr via AJAX"""
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        ilmiy_nashr = get_object_or_404(IlmiyNashr, id=ilmiy_nashr_id)
        ilmiy_nashr_name = ilmiy_nashr.name

        ilmiy_nashr.delete()

        logger.info(f"IlmiyNashr '{ilmiy_nashr_name}' deleted successfully")
        return JsonResponse({
            'success': True,
            'message': "Ilmiy nashr turi muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting IlmiyNashr {ilmiy_nashr_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# NAVIGATION MANAGEMENT (if needed)
@require_admin_login
def navigation_publishers_page(request):
    """Navigation for Publishers management page"""
    try:
        navigations = Navigation_For_Publishers_Page.objects.all()
        context = {
            'navigations': navigations,
            'page_title': 'Nashriyotchilar uchun Navigatsiya',
            'page_description': 'Nashriyotchilar sahifasi navigatsiyasini boshqarish'
        }
        return render(request, 'for_publishers.html', context)
    except Exception as e:
        logger.error(f"Error in navigation_publishers_page: {e}")
        messages.error(request, f'Sahifa yuklashda xatolik: {str(e)}')
        return redirect('admin_dashboard')


@require_admin_login
@csrf_protect
@transaction.atomic
def add_navigation_ajax(request):
    """Add navigation via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        name = request.POST.get('name', '').strip()

        if not name:
            return JsonResponse({'success': False, 'error': "Nom majburiy"})

        if Navigation_For_Publishers_Page.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': "Bu nom allaqachon mavjud"})

        navigation = Navigation_For_Publishers_Page.objects.create(name=name)

        # Add navigation items if provided
        items = request.POST.getlist('items[]')
        for item_text in items:
            if item_text.strip():
                Navigation_Item.objects.create(
                    navigation=navigation,
                    text=item_text.strip()
                )

        return JsonResponse({
            'success': True,
            'message': "Navigatsiya muvaffaqiyatli qo'shildi",
            'navigation_id': navigation.id
        })

    except Exception as e:
        logger.error(f"Error adding navigation: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
@csrf_protect
@transaction.atomic
def update_navigation_ajax(request, navigation_id):
    """Update navigation via AJAX"""
    if request.method == 'POST':
        try:
            navigation = get_object_or_404(Navigation_For_Publishers_Page, id=navigation_id)
            navigation.name = request.POST.get('name', navigation.name).strip()
            navigation.save()

            # Update navigation items
            Navigation_Item.objects.filter(navigation=navigation).delete()

            # Add new items
            items = request.POST.getlist('items[]')
            for item_text in items:
                if item_text.strip():
                    Navigation_Item.objects.create(
                        navigation=navigation,
                        text=item_text.strip()
                    )

            return JsonResponse({
                'success': True,
                'message': "Navigatsiya yangilandi"
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            navigation = get_object_or_404(Navigation_For_Publishers_Page, id=navigation_id)
            items = Navigation_Item.objects.filter(navigation=navigation)

            navigation_data = {
                'id': navigation.id,
                'name': navigation.name,
                'items': [{'id': item.id, 'text': item.text} for item in items]
            }

            return JsonResponse({'success': True, 'navigation': navigation_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


@require_admin_login
@csrf_protect
@transaction.atomic
def delete_navigation_ajax(request, navigation_id):
    """Delete navigation via AJAX"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        navigation = get_object_or_404(Navigation_For_Publishers_Page, id=navigation_id)
        navigation_name = navigation.name

        # Delete all related items (cascade will handle this, but being explicit)
        Navigation_Item.objects.filter(navigation=navigation).delete()

        # Delete the navigation
        navigation.delete()

        logger.info(f"Navigation '{navigation_name}' deleted successfully")

        return JsonResponse({
            'success': True,
            'message': "Navigatsiya muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting navigation {navigation_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
def navigation_list_ajax(request):
    """Get list of navigations for AJAX requests"""
    try:
        navigations = Navigation_For_Publishers_Page.objects.annotate(
            item_count=Count('navigation_item')
        ).order_by('name')

        navigations_data = []
        for navigation in navigations:
            items = Navigation_Item.objects.filter(navigation=navigation)
            navigations_data.append({
                'id': navigation.id,
                'name': navigation.name,
                'item_count': navigation.item_count,
                'items': [{'id': item.id, 'text': item.text} for item in items]
            })

        return JsonResponse({'success': True, 'navigations': navigations_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
def toggle_article_featured(request, article_id):
    """Toggle article featured status"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        article = get_object_or_404(Article, id=article_id)
        article.featured = not getattr(article, 'featured', False)
        article.save(update_fields=['featured'])
        return JsonResponse({
            'success': True,
            'featured': article.featured,
            'message': f"Maqola {'tanlangan' if article.featured else 'oddiy'} holatga o'tkazildi"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
