import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import *
import logging

from main.admin_views import require_admin_login
from .utils import send_diploma_email

logger = logging.getLogger(__name__)


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


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_add_article_ajax(request, journal_id):
    """Add article to the currently active issue of a specific journal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal = get_object_or_404(Journal, id=journal_id)

        title = request.POST.get('title', '').strip()
        subtitle = request.POST.get('subtitle', '').strip()
        abstract = request.POST.get('abstract', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        date_published = request.POST.get('date_published')
        first_page = request.POST.get('first_page')
        last_page = request.POST.get('last_page')
        meta_description = request.POST.get('meta_description', '').strip()
        doi = request.POST.get('doi', '').strip()
        references = request.POST.get('references', '').strip()
        featured = request.POST.get('featured') == 'on'
        open_access = request.POST.get('open_access') == 'on'
        is_published = request.POST.get('is_published') == 'off'
        language = request.POST.get('language', 'uz')

        # Author data
        first_names = request.POST.getlist('author_first_name[]')
        middle_names = request.POST.getlist('author_middle_name[]')
        last_names = request.POST.getlist('author_last_name[]')
        affiliations = request.POST.getlist('author_affiliation[]')
        emails = request.POST.getlist('author_email[]')
        orcids = request.POST.getlist('author_orcid[]')

        # Validation
        if not title:
            return JsonResponse({'success': False, 'error': "Sarlavha majburiy"})
        if not abstract:
            return JsonResponse({'success': False, 'error': "Abstrakt majburiy"})
        if not first_names or not last_names or not first_names[0].strip() or not last_names[0].strip():
            return JsonResponse({'success': False, 'error': "Kamida bitta muallif ko'rsatish majburiy"})

        # Always attach to the active issue for this journal
        issue = Issue.objects.filter(journal=journal, is_active=True).order_by('-year', '-volume', '-number').first()
        if not issue:
            return JsonResponse({'success': False, 'error': "Faol son topilmadi. Avval yangi son yarating."})

        # Handle PDF file upload
        pdf_file = request.FILES.get('pdf_file')
        main_pdf = None
        if pdf_file:
            try:
                file_obj = File.objects.create(
                    original_filename=pdf_file.name,
                    file_size=pdf_file.size,
                    mime_type=pdf_file.content_type or 'application/pdf',
                    file_type='pdf',
                    description='Main article PDF'
                )
                file_obj.file.save(pdf_file.name, pdf_file)
                main_pdf = file_obj
            except Exception as e:
                return JsonResponse({'success': False, 'error': f"PDF yuklashda xato: {str(e)}"})

        # Generate unique slug
        base_slug = slugify(title)[:200]
        slug = base_slug
        counter = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        article = Article.objects.create(
            issue=issue,
            title=title,
            subtitle=subtitle if subtitle else None,
            abstract=abstract,
            keywords=keywords if keywords else None,
            slug=slug,
            date_published=date_published if date_published else timezone.now().date(),
            first_page=int(first_page) if first_page else None,
            last_page=int(last_page) if last_page else None,
            main_pdf=main_pdf,
            meta_description=meta_description if meta_description else None,
            references=references if references else None,
            doi=doi if doi else None,
            featured=featured,
            open_access=open_access,
            language=language,
            is_published=is_published,
            views=0,
            downloads=0
        )

        old_is_published = article.is_published

        # Add authors
        for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
            if not first_name.strip() or not last_name.strip():
                continue

            middle_name = middle_names[i] if i < len(middle_names) else ''
            affiliation = affiliations[i] if i < len(affiliations) else ''
            email = emails[i] if i < len(emails) else ''
            orcid = orcids[i] if i < len(orcids) else ''

            author = _create_or_update_author(
                first_name.strip(),
                last_name.strip(),
                middle_name.strip(),
                affiliation.strip(),
                email.strip(),
                orcid.strip()
            )
            ArticleAuthor.objects.create(
                article=article,
                author=author,
                order=i,
                is_corresponding=(i == 0)
            )

        if (not old_is_published) and article.is_published and (not article.diploma_sent):
            article.diploma_sent = True
            article.save(update_fields=['diploma_sent'])

            try:
                send_diploma_email(article)
                logger.info(f"Diploma email sent for article ID {article.id} titled '{article.title}'")
            except Exception as email_error:
                logger.error(f"Failed to send diploma email while creating for article ID {article.id}: {email_error}")

        return JsonResponse({
            'success': True,
            'message': "Maqola muvaffaqiyatli qo'shildi",
            'article_id': article.id
        })

    except Exception as e:
        logger.error(f"Error in journal_add_article_ajax: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
@csrf_protect
@transaction.atomic
def update_article_ajax(request, article_id):
    """Update article via AJAX"""
    if request.method == 'POST':
        try:
            article = get_object_or_404(Article, id=article_id)

            old_is_published = article.is_published

            article.title = request.POST.get('title', article.title).strip()
            article.subtitle = request.POST.get('subtitle', '').strip() or None
            article.abstract = request.POST.get('abstract', article.abstract).strip()
            article.keywords = request.POST.get('keywords', '').strip() or None
            article.meta_description = request.POST.get('meta_description', '').strip() or None
            article.references = request.POST.get('references', '').strip() or None
            article.doi = request.POST.get('doi', '').strip() or None
            article.language = request.POST.get('language', article.language)
            article.featured = request.POST.get('featured') == 'on'
            article.open_access = request.POST.get('open_access') == 'on'
            article.is_published = request.POST.get('is_published') == 'on'

            date_published = request.POST.get('date_published')
            if date_published:
                article.date_published = date_published

            first_page = request.POST.get('first_page', '').strip()
            last_page = request.POST.get('last_page', '').strip()

            article.first_page = int(first_page) if first_page else None
            article.last_page = int(last_page) if last_page else None

            # Handle PDF file upload
            pdf_file = request.FILES.get('pdf_file')
            if pdf_file:
                try:
                    if article.main_pdf:
                        if article.main_pdf.file:
                            article.main_pdf.file.delete()
                        article.main_pdf.delete()

                    file_obj = File.objects.create(
                        original_filename=pdf_file.name,
                        file_size=pdf_file.size,
                        mime_type=pdf_file.content_type or 'application/pdf',
                        file_type='pdf',
                        description='Main article PDF'
                    )
                    file_obj.file.save(pdf_file.name, pdf_file)
                    article.main_pdf = file_obj
                except Exception as e:
                    logger.error(f"PDF upload error: {e}")
                    return JsonResponse({'success': False, 'error': f"PDF yuklashda xato: {str(e)}"})

            # Update slug if title changed
            original_title = Article.objects.get(id=article.id).title
            if article.title != original_title:
                base_slug = slugify(article.title)[:200]
                slug = base_slug
                counter = 1
                while Article.objects.filter(slug=slug).exclude(id=article.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                article.slug = slug

            article.save()

            # Update authors
            first_names = request.POST.getlist('author_first_name[]')
            if first_names and first_names[0].strip():
                ArticleAuthor.objects.filter(article=article).delete()

                middle_names = request.POST.getlist('author_middle_name[]')
                last_names = request.POST.getlist('author_last_name[]')
                affiliations = request.POST.getlist('author_affiliation[]')
                emails = request.POST.getlist('author_email[]')
                orcids = request.POST.getlist('author_orcid[]')

                for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
                    if not first_name.strip() or not last_name.strip():
                        continue

                    middle_name = middle_names[i] if i < len(middle_names) else ''
                    affiliation = affiliations[i] if i < len(affiliations) else ''
                    email = emails[i] if i < len(emails) else ''
                    orcid = orcids[i] if i < len(orcids) else ''

                    author = _create_or_update_author(first_name.strip(), last_name.strip(),
                                                      middle_name.strip(), affiliation.strip(),
                                                      email.strip(), orcid.strip())
                    ArticleAuthor.objects.create(
                        article=article,
                        author=author,
                        order=i,
                        is_corresponding=(i == 0)
                    )

            # sending diploam section
            if (not old_is_published) and article.is_published and (not article.diploma_sent):
                article.diploma_sent = True
                article.save(update_fields=['diploma_sent'])

                try:
                    send_diploma_email(article)
                    logger.info(f"Diploma email sent for article ID {article.id} titled '{article.title}'")
                except Exception as email_error:
                    logger.error(f"Failed to send diploma email for article ID {article.id}: {email_error}")

            logger.info(f"Article {article.id} updated successfully")

            return JsonResponse({
                'success': True,
                'message': "Maqola muvaffaqiyatli yangilandi",
                'article_id': article.id
            })

        except ValueError:
            return JsonResponse({'success': False, 'error': 'Raqamli maydonlarda noto\'g\'ri qiymat'})
        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})

    elif request.method == 'GET':
        try:
            article = get_object_or_404(Article, id=article_id)

            authors_data = []
            try:
                article_authors = ArticleAuthor.objects.filter(article=article).order_by('order')
                for aa in article_authors:
                    authors_data.append({
                        'id': aa.author.id,
                        'first_name': aa.author.first_name,
                        'middle_name': getattr(aa.author, 'middle_name', '') or '',
                        'last_name': aa.author.last_name,
                        'email': getattr(aa.author, 'email', '') or '',
                        'affiliation': getattr(aa.author, 'affiliation', '') or '',
                        'orcid': getattr(aa.author, 'orcid', '') or '',
                        'order': aa.order,
                        'is_corresponding': aa.is_corresponding
                    })
            except Exception as e:
                logger.error(f"Error getting authors for article {article_id}: {e}")

            article_data = {
                'id': article.id,
                'title': article.title,
                'subtitle': getattr(article, 'subtitle', '') or '',
                'abstract': article.abstract,
                'keywords': article.keywords or '',
                'language': getattr(article, 'language', 'uz'),
                'doi': article.doi or '',
                'date_published': article.date_published.strftime('%Y-%m-%d'),
                'first_page': article.first_page,
                'last_page': article.last_page,
                'featured': getattr(article, 'featured', False),
                'open_access': getattr(article, 'open_access', False),
                'is_published': article.is_published,
                'meta_description': getattr(article, 'meta_description', '') or '',
                'references': getattr(article, 'references', '') or '',
                'journal_id': article.issue.journal.id if article.issue else None,
                'issue_id': article.issue.id if article.issue else None,
                'authors': authors_data,
                'has_pdf': bool(article.main_pdf)
            }

            return JsonResponse({
                'success': True,
                'article': article_data
            })

        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


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


@require_admin_login
def get_active_issue_ajax(request, journal_id):
    journal = get_object_or_404(Journal, id=journal_id)
    issue = Issue.objects.filter(journal=journal, is_active=True).order_by('-year', '-volume', '-number').first()
    if not issue:
        return JsonResponse({'success': False, 'error': 'Faol son topilmadi!'})
    return JsonResponse({
        'success': True,
        'issue': {
            'id': issue.id,
            'volume': issue.volume,
            'number': issue.number,
            'year': issue.year,
            'title': issue.title,
        }
    })


@require_admin_login
def journal_editors_ajax(request, journal_id):
    try:
        journal = get_object_or_404(Journal, id=journal_id)

        editors = JournalEditor.objects.filter(journal_id=journal_id).order_by('editor_type', 'last_name')

        editors_data = []
        for editor in editors:
            editors_data.append({
                'id': editor.id,
                'full_name': editor.full_name,
                'short_name': editor.short_name,
                'first_name': editor.first_name,
                'middle_name': editor.middle_name or '',
                'last_name': editor.last_name,
                'title': editor.title or '',
                'affiliation': editor.affiliation or '',
                'position': editor.position or '',
                'editor_type': editor.editor_type,
                'editor_type_display': editor.get_editor_type_display(),
                'is_active': editor.is_active,
                'created_at': editor.created_at.strftime('%d.%m.%Y')
            })

        return JsonResponse({
            'success': True,
            'editors': editors_data
        })

    except Exception as e:
        logger.error(f"Error getting editors for journal {journal_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_add_editor_ajax(request, journal_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        journal = get_object_or_404(Journal, id=journal_id)

        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        title = request.POST.get('title', '').strip()
        affiliation = request.POST.get('affiliation', '').strip()
        position = request.POST.get('position', '').strip()
        editor_type = request.POST.get('editor_type', 'associate')
        is_active = request.POST.get('is_active') == 'on'

        if not first_name or not last_name:
            return JsonResponse({'success': False, 'error': "Ism va familiya majburiy"})

        editor = JournalEditor.objects.create(
            journal_id=journal_id,
            first_name=first_name,
            middle_name=middle_name if middle_name else None,
            last_name=last_name,
            title=title if title else None,
            affiliation=affiliation if affiliation else None,
            position=position if position else None,
            editor_type=editor_type,
            is_active=is_active,
        )

        logger.info(f"Editor {editor.full_name} added to journal {journal.title}")

        return JsonResponse({
            'success': True,
            'message': "Muharrir muvaffaqiyatli qo'shildi",
            'editor_id': editor.id
        })

    except Exception as e:
        logger.error(f"Error adding editor to journal {journal_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_update_editor_ajax(request, journal_id, editor_id):
    """Update editor for specific journal"""
    if request.method == 'POST':
        try:
            # Verify journal and editor exist
            journal = get_object_or_404(Journal, id=journal_id)
            editor = get_object_or_404(JournalEditor, id=editor_id, journal_id=journal_id)

            # Update fields
            editor.first_name = request.POST.get('first_name', editor.first_name).strip()
            editor.middle_name = request.POST.get('middle_name', '').strip() or None
            editor.last_name = request.POST.get('last_name', editor.last_name).strip()
            editor.title = request.POST.get('title', '').strip() or None
            editor.affiliation = request.POST.get('affiliation', '').strip() or None
            editor.position = request.POST.get('position', '').strip() or None
            editor.editor_type = request.POST.get('editor_type', editor.editor_type)
            editor.is_active = request.POST.get('is_active') == 'on'

            editor.save()

            return JsonResponse({
                'success': True,
                'message': "Muharrir ma'lumotlari yangilandi"
            })

        except Exception as e:
            logger.error(f"Error updating editor {editor_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            # Verify journal and editor exist
            journal = get_object_or_404(Journal, id=journal_id)
            editor = get_object_or_404(JournalEditor, id=editor_id, journal_id=journal_id)

            editor_data = {
                'id': editor.id,
                'first_name': editor.first_name,
                'middle_name': editor.middle_name or '',
                'last_name': editor.last_name,
                'title': editor.title or '',
                'affiliation': editor.affiliation or '',
                'position': editor.position or '',
                'editor_type': editor.editor_type,
                'is_active': editor.is_active,
            }

            return JsonResponse({'success': True, 'editor': editor_data})

        except Exception as e:
            logger.error(f"Error getting editor {editor_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_delete_editor_ajax(request, journal_id, editor_id):
    """Delete editor from specific journal"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        # Verify journal and editor exist
        journal = get_object_or_404(Journal, id=journal_id)
        editor = get_object_or_404(JournalEditor, id=editor_id, journal_id=journal_id)
        editor_name = editor.full_name

        # Delete the editor
        editor.delete()

        logger.info(f"Editor '{editor_name}' deleted from journal {journal.title}")

        return JsonResponse({
            'success': True,
            'message': "Muharrir muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting editor {editor_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


# ===============================
# JOURNAL POLICIES MANAGEMENT
# ===============================

@require_admin_login
def journal_policies_ajax(request, journal_id):
    """Get policies for specific journal"""
    try:
        # Verify journal exists
        journal = get_object_or_404(Journal, id=journal_id)

        # Get all policies for this journal
        policies = JournalPolicy.objects.filter(journal=journal).order_by('order', 'policy_type')

        policies_data = []
        for policy in policies:
            policies_data.append({
                'id': policy.id,
                'policy_type': policy.policy_type,
                'policy_type_display': policy.get_policy_type_display(),
                'title': policy.title,
                'content': policy.content,
                'content_preview': policy.content_preview,
                'short_description': policy.short_description or '',
                'requirements': policy.requirements or '',
                'examples': policy.examples or '',
                'is_active': policy.is_active,
                'is_public': policy.is_public,
                'order': policy.order,
                'language': policy.language,
                'meta_description': policy.meta_description or '',
                'keywords': policy.keywords or '',
                'version': policy.version,
                'effective_date': policy.effective_date.strftime('%Y-%m-%d'),
                'last_updated': policy.last_updated.strftime('%d.%m.%Y %H:%M'),
                'created_by': policy.created_by or '',
                'updated_by': policy.updated_by or '',
                'word_count': policy.word_count,
                'created_at': policy.created_at.strftime('%d.%m.%Y')
            })

        return JsonResponse({
            'success': True,
            'policies': policies_data
        })

    except Exception as e:
        logger.error(f"Error getting policies for journal {journal_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_add_policy_ajax(request, journal_id):
    """Add policy to specific journal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        # Verify journal exists
        journal = get_object_or_404(Journal, id=journal_id)

        # Get form data
        policy_type = request.POST.get('policy_type')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        short_description = request.POST.get('short_description', '').strip()
        requirements = request.POST.get('requirements', '').strip()
        examples = request.POST.get('examples', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_public = request.POST.get('is_public') == 'on'
        order = request.POST.get('order', 0)
        language = request.POST.get('language', 'uz')
        meta_description = request.POST.get('meta_description', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        version = request.POST.get('version', '1.0').strip()
        effective_date = request.POST.get('effective_date')
        created_by = request.session.get('admin_username', 'Admin')

        # Validation
        if not policy_type:
            return JsonResponse({'success': False, 'error': "Siyosat turi majburiy"})
        if not content:
            return JsonResponse({'success': False, 'error': "Mazmun majburiy"})

        # Check if policy type already exists for this journal
        if JournalPolicy.objects.filter(journal=journal, policy_type=policy_type).exists():
            return JsonResponse({'success': False, 'error': "Bu siyosat turi allaqachon mavjud"})

        # Auto-generate title if not provided
        if not title:
            title = dict(JournalPolicy.POLICY_TYPES).get(policy_type, policy_type)

        # Create policy
        policy = JournalPolicy.objects.create(
            journal=journal,
            policy_type=policy_type,
            title=title,
            content=content,
            short_description=short_description if short_description else None,
            requirements=requirements if requirements else None,
            examples=examples if examples else None,
            is_active=is_active,
            is_public=is_public,
            order=int(order) if order else 0,
            language=language,
            meta_description=meta_description if meta_description else None,
            keywords=keywords if keywords else None,
            version=version,
            effective_date=effective_date if effective_date else timezone.now().date(),
            created_by=created_by
        )

        logger.info(f"Policy {policy.title} added to journal {journal.title}")

        return JsonResponse({
            'success': True,
            'message': "Siyosat muvaffaqiyatli qo'shildi",
            'policy_id': policy.id
        })

    except Exception as e:
        logger.error(f"Error adding policy to journal {journal_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_update_policy_ajax(request, journal_id, policy_id):
    """Update policy for specific journal"""
    if request.method == 'POST':
        try:
            # Verify journal and policy exist
            journal = get_object_or_404(Journal, id=journal_id)
            policy = get_object_or_404(JournalPolicy, id=policy_id, journal=journal)

            # Update fields
            policy.policy_type = request.POST.get('policy_type', policy.policy_type)
            policy.title = request.POST.get('title', policy.title).strip()
            policy.content = request.POST.get('content', policy.content).strip()
            policy.short_description = request.POST.get('short_description', '').strip() or None
            policy.requirements = request.POST.get('requirements', '').strip() or None
            policy.examples = request.POST.get('examples', '').strip() or None
            policy.is_active = request.POST.get('is_active') == 'on'
            policy.is_public = request.POST.get('is_public') == 'on'
            policy.order = int(request.POST.get('order', policy.order))
            policy.language = request.POST.get('language', policy.language)
            policy.meta_description = request.POST.get('meta_description', '').strip() or None
            policy.keywords = request.POST.get('keywords', '').strip() or None
            policy.version = request.POST.get('version', policy.version).strip()
            policy.updated_by = request.session.get('admin_username', 'Admin')

            effective_date = request.POST.get('effective_date')
            if effective_date:
                policy.effective_date = effective_date

            policy.save()

            return JsonResponse({
                'success': True,
                'message': "Siyosat ma'lumotlari yangilandi"
            })

        except Exception as e:
            logger.error(f"Error updating policy {policy_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    elif request.method == 'GET':
        try:
            # Verify journal and policy exist
            journal = get_object_or_404(Journal, id=journal_id)
            policy = get_object_or_404(JournalPolicy, id=policy_id, journal=journal)

            policy_data = {
                'id': policy.id,
                'policy_type': policy.policy_type,
                'title': policy.title,
                'content': policy.content,
                'short_description': policy.short_description or '',
                'requirements': policy.requirements or '',
                'examples': policy.examples or '',
                'is_active': policy.is_active,
                'is_public': policy.is_public,
                'order': policy.order,
                'language': policy.language,
                'meta_description': policy.meta_description or '',
                'keywords': policy.keywords or '',
                'version': policy.version,
                'effective_date': policy.effective_date.strftime('%Y-%m-%d'),
                'created_by': policy.created_by or '',
                'updated_by': policy.updated_by or ''
            }

            return JsonResponse({'success': True, 'policy': policy_data})

        except Exception as e:
            logger.error(f"Error getting policy {policy_id}: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})


@require_admin_login
@csrf_protect
@transaction.atomic
def journal_delete_policy_ajax(request, journal_id, policy_id):
    """Delete policy from specific journal"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov"})

    try:
        # Verify journal and policy exist
        journal = get_object_or_404(Journal, id=journal_id)
        policy = get_object_or_404(JournalPolicy, id=policy_id, journal=journal)
        policy_title = policy.title

        # Delete the policy
        policy.delete()

        logger.info(f"Policy '{policy_title}' deleted from journal {journal.title}")

        return JsonResponse({
            'success': True,
            'message': "Siyosat muvaffaqiyatli o'chirildi"
        })

    except Exception as e:
        logger.error(f"Error deleting policy {policy_id}: {e}")
        return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})


# ===============================
# UTILITY FUNCTIONS
# ===============================

@require_admin_login
def get_editor_types(request):
    """Get available editor types"""
    try:
        editor_types = [
            {'value': key, 'label': value}
            for key, value in JournalEditor.EDITOR_TYPES
        ]
        return JsonResponse({
            'success': True,
            'editor_types': editor_types
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def get_policy_types(request):
    """Get available policy types"""
    try:
        policy_types = [
            {'value': key, 'label': value}
            for key, value in JournalPolicy.POLICY_TYPES
        ]
        return JsonResponse({
            'success': True,
            'policy_types': policy_types
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===============================
# EXPORT FUNCTIONS
# ===============================

@require_admin_login
def export_journal_editors_csv(request, journal_id):
    """Export journal editors to CSV"""
    try:
        journal = get_object_or_404(Journal, id=journal_id)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{journal.url_slug}_editors_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Full Name', 'Editor Type', 'Title', 'Affiliation',
            'Position', 'Active', 'Order', 'Created At'
        ])

        editors = JournalEditor.objects.filter(journal_id=journal_id).order_by('order', 'last_name')
        for editor in editors:
            writer.writerow([
                editor.id,
                editor.full_name,
                editor.get_editor_type_display(),
                editor.title or '',
                editor.affiliation or '',
                editor.position or '',
                'Yes' if editor.is_active else 'No',
                editor.order,
                editor.created_at.strftime('%Y-%m-%d')
            ])

        return response

    except Exception as e:
        logger.error(f"Error exporting editors: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@require_admin_login
def export_journal_policies_csv(request, journal_id):
    try:
        journal = get_object_or_404(Journal, id=journal_id)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{journal.url_slug}_policies_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Policy Type', 'Title', 'Content Preview', 'Language',
            'Version', 'Active', 'Public', 'Effective Date', 'Last Updated',
            'Word Count', 'Created By', 'Updated By'
        ])

        policies = JournalPolicy.objects.filter(journal=journal).order_by('order', 'policy_type')
        for policy in policies:
            writer.writerow([
                policy.id,
                policy.get_policy_type_display(),
                policy.title,
                policy.content_preview,
                policy.get_language_display(),
                policy.version,
                'Yes' if policy.is_active else 'No',
                'Yes' if policy.is_public else 'No',
                policy.effective_date.strftime('%Y-%m-%d'),
                policy.last_updated.strftime('%Y-%m-%d %H:%M'),
                policy.word_count,
                policy.created_by or '',
                policy.updated_by or ''
            ])

        return response

    except Exception as e:
        logger.error(f"Error exporting policies: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
