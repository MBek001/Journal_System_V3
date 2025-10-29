import requests
from django.core.mail import EmailMessage

from main.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SITE_DOMAIN
import os

from main.diploma import create_diploma
from main.models import ArticleAuthor
from django.conf import settings


def send_diploma_email(article):

    template_path = os.path.join(settings.MEDIA_ROOT, "diploma", "original.pptx")

    journal_name = article.issue.journal.title if article.issue else "Noma’lum jurnal"
    issue_number = article.issue.number if article.issue else "?"
    journal_url = article.issue.journal.slug if article.issue and hasattr(article.issue.journal, "slug") else "journal"
    article_url = f"{SITE_DOMAIN}/{journal_url}/{article.slug}/"
    pub_date = article.date_published

    for aa in ArticleAuthor.objects.filter(article=article).select_related("author"):
        author = aa.author

        # ✅ Use Author model's email
        recipient_email = author.email
        if not recipient_email:
            continue

        output_path = os.path.join(settings.MEDIA_ROOT, "diploma", f"diploma_{author.full_name}.pptx")

        diploma_file = create_diploma(
            author_name=author.full_name,
            journal_name=journal_name,
            issue_number=issue_number,
            article_url=article_url,
            pub_date=pub_date,
            template_path=template_path,
            output_path=output_path,
        )

        subject = f"Tabriklaymiz! Sizning maqolangiz nashr etildi: {article.title}"
        body = (
            f"Assalomu alaykum, {author.full_name}!\n\n"
            f"Sizning maqolangiz «{journal_name}» jurnalining {issue_number}-sonida nashr qilindi.\n\n"
            f"Batafsil maqola: {article_url}"
        )

        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
        )
        email.attach_file(diploma_file)
        email.send(fail_silently=False)


def send_to_telegram(message, files=None):
    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
        data={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    )

    if files:
        for f in files:
            try:
                with open(f.file.path, 'rb') as doc:
                    requests.post(
                        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument',
                        data={'chat_id': TELEGRAM_CHAT_ID},
                        files={'document': doc}
                    )
            except Exception as e:
                print(f"❌ File send error: {e}")
