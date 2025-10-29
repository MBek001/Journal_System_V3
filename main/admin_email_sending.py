import logging
from typing import List
import re
from html import unescape

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Q
from django.utils.html import strip_tags

from .admin_views import require_admin_login
from .models import Author
from .forms import MessageAuthorForm

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def _chunk_list(items: List[str], size: int) -> List[List[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _html_to_plain_text(html_content):
    """Convert HTML content to plain text for email fallback"""
    # Remove HTML tags
    plain_text = strip_tags(html_content)
    # Unescape HTML entities
    plain_text = unescape(plain_text)
    # Clean up extra whitespace
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    return plain_text


@require_admin_login
def message_authors_view(request, author_id=None):
    initial_data = {}
    if author_id:
        try:
            author = get_object_or_404(Author, pk=author_id)
            # Fix: Pass the author object, not a list
            initial_data['authors'] = [author.pk]  # Pass the ID, not the object
            initial_data['send_to_all'] = False
        except Author.DoesNotExist:
            messages.error(request, "Author not found.")
            return redirect('message_authors')

    if request.method == 'POST':
        form = MessageAuthorForm(request.POST)
        if form.is_valid():
            send_to_all = form.cleaned_data['send_to_all']
            selected_authors_qs = form.cleaned_data['authors']
            subject = form.cleaned_data['subject'].strip()
            message_html = form.cleaned_data['message'].strip()

            # Convert HTML to plain text for fallback
            message_plain = _html_to_plain_text(message_html)

            # Compute recipients
            if send_to_all:
                recipients_qs = Author.objects.filter(
                    is_active=True
                ).filter(
                    Q(email__isnull=False) & ~Q(email__exact="")
                )
                success_scope = "all active authors"
            else:
                recipients_qs = selected_authors_qs.filter(
                    Q(email__isnull=False) & ~Q(email__exact="")
                )
                success_scope = "the selected authors"

            recipient_emails = sorted({a.email.strip() for a in recipients_qs if a.email and '@' in a.email})
            total_recipients = len(recipient_emails)

            if total_recipients == 0:
                messages.warning(request, "No valid email addresses found among the chosen recipients.")
                authors = Author.objects.filter(is_active=True).order_by('last_name', 'first_name')
                return render(request, 'admin_message_authors.html', {
                    'form': form,
                    'authors': authors,
                    'author_id': author_id,  # Pass author_id to template
                    'page_title': 'Message Author(s)'
                })

            try:
                with get_connection() as connection:
                    batches = _chunk_list(recipient_emails, BATCH_SIZE)
                    sent_batches = 0
                    for chunk in batches:
                        email = EmailMultiAlternatives(
                            subject=subject,
                            body=message_plain,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[],
                            bcc=chunk,
                            connection=connection,
                        )
                        email.attach_alternative(message_html, "text/html")
                        email.send(fail_silently=False)
                        sent_batches += 1
                        logger.info(f"Sent batch {sent_batches}/{len(batches)} ({len(chunk)} recipients)")

                messages.success(
                    request,
                    f"Email has been sent successfully ✅ "
                )

            except Exception as e:
                logger.exception("Email sending failed")
                messages.error(request, f"Error sending message: {e}")
                authors = Author.objects.filter(is_active=True).order_by('last_name', 'first_name')
                return render(request, 'admin_message_authors.html', {
                    'form': form,
                    'authors': authors,
                    'author_id': author_id,  # Pass author_id to template
                    'page_title': 'Message Author(s)'
                })

            if author_id:
                return redirect('message_author_single', author_id=author_id)
            return redirect('message_authors')
        else:
            pass
    else:
        form = MessageAuthorForm(initial=initial_data)

    # Get authors for template context
    authors = Author.objects.filter(is_active=True).order_by('last_name', 'first_name')

    context = {
        'form': form,
        'authors': authors,
        'author_id': author_id,  # Pass author_id to template
        'page_title': 'Message Author(s)'
    }
    return render(request, 'admin_message_authors.html', context)