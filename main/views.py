import re
from datetime import datetime

from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
import mimetypes
from main.forms import ContactForm
from main.models import *
from main.utils import send_to_telegram, send_diploma_email

from django.db.models import Q, Value, F, Exists, OuterRef, Count, Max, Min
from django.db.models.functions import Concat
from django.shortcuts import render


def global_search(request):
    q = (request.GET.get('q') or '').strip()
    journal_results = article_results = author_results = []
    journal_count = article_count = author_count = total_results = 0

    if len(q) >= 2:
        tokens = [t for t in q.split() if t]

        # Journals
        j_q = Q()
        for t in tokens:
            j_q &= (Q(title__icontains=t) | Q(description__icontains=t) | Q(meta_keywords__icontains=t))
        journal_results = Journal.objects.only('id', 'title', 'url_slug').filter(j_q)

        # Authors — rename annotations to avoid 'full_name' clash
        authors_qs = Author.objects.annotate(
            full_name_text=Concat(F('first_name'), Value(' '), F('middle_name'), Value(' '), F('last_name')),
            full_name_rev_text=Concat(F('last_name'), Value(' '), F('first_name')),
        )

        a_q = Q()
        for t in tokens:
            a_q &= (
                    Q(first_name__icontains=t) |
                    Q(middle_name__icontains=t) |
                    Q(last_name__icontains=t) |
                    Q(full_name_text__icontains=t) |
                    Q(full_name_rev_text__icontains=t) |
                    Q(affiliation__icontains=t)
            )

        author_results = (authors_qs
                          .filter(a_q)
                          .only('id', 'first_name', 'middle_name', 'last_name', 'affiliation', 'photo')
                          .distinct())

        # Articles — use EXISTS for matching authors; no annotation-name clashes here
        author_sub_q = Q()
        for t in tokens:
            author_sub_q &= (
                    Q(first_name__icontains=t) |
                    Q(middle_name__icontains=t) |
                    Q(last_name__icontains=t)
            )

        matching_authors = Author.objects.filter(
            articleauthor__article=OuterRef('pk')
        ).filter(author_sub_q)

        art_q = Q()
        for t in tokens:
            art_q &= (
                    Q(title__icontains=t) |
                    Q(abstract__icontains=t) |
                    Q(keywords__icontains=t)
            )

        article_results = (Article.objects
                           .select_related('issue__journal')
                           .prefetch_related('authors')
                           .filter(art_q | Exists(matching_authors))
                           .only('id', 'slug', 'title', 'abstract', 'created_at', 'issue')
                           .distinct())

        # counts
        journal_count = journal_results.count()
        author_count = author_results.count()
        article_count = article_results.count()
        total_results = journal_count + author_count + article_count

    return render(request, 'global_search.html', {
        'q': q,
        'journal_results': journal_results,
        'article_results': article_results,
        'author_results': author_results,
        'journal_count': journal_count,
        'article_count': article_count,
        'author_count': author_count,
        'total_results': total_results,
        'page_title': 'Qidiruv natijalari',
    })


def authors_list(request):
    authors = Author.objects.filter(is_active=True).annotate(
        article_count=Count('article')
    ).order_by('last_name', 'first_name')

    # Handle search query
    search_query = request.GET.get('q', '').strip()
    if search_query:
        authors = authors.filter(
            first_name__icontains=search_query
        ) | authors.filter(last_name__icontains=search_query)

    context = {
        'authors': authors,
        'unique_affiliations': Author.objects.filter(
            is_active=True
        ).values('affiliation').distinct().count(),
        'total_articles': Article.objects.filter(is_published=True).count(),
    }
    return render(request, 'authors_list.html', context)


def journals_list(request):
    # Boshlang'ich queryset
    journals = Journal.objects.filter(is_active=True)

    # Qidiruv so'rovini olish
    search_query = request.GET.get('q', '').strip()

    # Agar qidiruv so'rovi bo'lsa, querysetni filtrlaymiz
    if search_query:
        journals = journals.filter(title__icontains=search_query)

    # Annotatsiya orqali statistikani hisoblaymiz
    # Har bir jurnal uchun kerakli ma'lumotlarni olish uchun annotate dan foydalanamiz
    journals = journals.annotate(
        total_issues=Count('issues', distinct=True, filter=models.Q(issues__is_published=True)),
        total_articles=Count('issues__articles', distinct=True, filter=models.Q(issues__articles__is_published=True)),
        first_issue_year=Min('issues__year', filter=models.Q(issues__is_published=True))  # Birinchi chiqqan yil
    ).prefetch_related(
        'issues__articles__authors'  # Kerakli related obyektlarni oldindan yuklash
    ).order_by('-created_at', 'title')

    # Umumiy statistika (barcha jurnallar bo'yicha, filtrdan keyin)
    total_issues = Issue.objects.filter(is_published=True, journal__in=journals).count()
    total_articles = Article.objects.filter(is_published=True, issue__journal__in=journals).count()
    active_journals = journals.count()

    context = {
        'journals': journals,  # Filtrlangan jurnallar
        'journal_stats': journals,  # Annotatsiya qilingan jurnallar (statistikalar bilan)
        'total_issues': total_issues,
        'total_articles': total_articles,
        'active_journals': active_journals,
        'search_query': search_query,  # Qidiruv so'rovini shablonga uzatamiz
    }

    return render(request, 'journals.html', context)


def home_view(request):
    latest_journals = Journal.objects.select_related().filter(
        is_active=True
    ).annotate(
        issues_count=Count('issues', filter=Q(issues__is_published=True), distinct=True),
        articles_count=Count('issues__articles', filter=Q(issues__is_published=True), distinct=True),
        latest_year=Max('issues__year', filter=Q(issues__is_published=True))
    ).order_by('-created_at')[:6]

    journal_stats = {
        'total_journals': Journal.objects.filter(is_active=True).count(),
        'total_issues': 0,
        'total_articles': 0,
        'total_authors': 0,
    }
    aggregated_stats = Journal.objects.filter(is_active=True).aggregate(
        total_issues=Count('issues', filter=Q(issues__is_published=True), distinct=True),
        total_articles=Count('issues__articles', filter=Q(issues__is_published=True), distinct=True),
    )
    journal_stats.update({
        'total_issues': aggregated_stats['total_issues'] or 0,
        'total_articles': aggregated_stats['total_articles'] or 0,
        'total_authors': Author.objects.filter(is_active=True).count(),  # Added author count
    })

    # Fetch recent articles with first author
    recent_articles = Article.objects.filter(is_published=True).order_by('-date_published')[:6]
    recent_articles_with_authors = []
    for article in recent_articles:
        first_author = article.author_list.first().author if article.author_list.exists() else None
        recent_articles_with_authors.append({
            'article': article,
            'first_author': first_author,
        })
    trending_journals = Journal.objects.select_related().filter(
        is_active=True
    ).annotate(
        issues_count=Count('issues', filter=Q(issues__is_published=True), distinct=True),
        articles_count=Count('issues__articles', filter=Q(issues__is_published=True), distinct=True),
    ).order_by('-issues_count', '-created_at')[:6]

    context = {
        'latest_journals': latest_journals,
        'trending_journals': trending_journals,  # Add this
        'journal_stats': journal_stats,
        'recent_articles': recent_articles_with_authors,
    }
    return render(request, 'index.html', context)


def about_view(request):
    return render(request, 'about.html')


def publisher_view(request):
    navigation_items = Navigation_For_Publishers_Page.objects.prefetch_related('navigation_item_set').all()

    context = {
        'navigation_items': navigation_items
    }
    return render(request, 'for_publishers.html', context)


def article_view(request):
    fanlar = FanTarmoq.objects.all()
    nashrlar = IlmiyNashr.objects.all()

    if request.method == 'POST':
        fan_id = request.POST.get('fan', '').strip()
        ilm_id = request.POST.get('ilm', '').strip()
        author = request.POST.get('author', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        description = request.POST.get('description', '').strip()
        files = request.FILES.getlist('article_file')

        # Debug: Log all received data
        print("POST data:", dict(request.POST))
        print("FILES:", [f.name for f in files if f] or "No files received")
        print("Content-Type:", request.META.get('CONTENT_TYPE', ''))

        # Validate required fields
        form_errors = {}
        if not fan_id:
            form_errors['fan'] = "Fan tarmoqini tanlang."
        if not ilm_id:
            form_errors['ilm'] = "Ilmiy nashrni tanlang."
        if not author:
            form_errors['author'] = "Muallif ismini kiriting."
        if not email:
            form_errors['email'] = "Email manzilini kiriting."
        if not phone:
            form_errors['phone'] = "Telefon raqamini kiriting."
        if not files:
            form_errors['files'] = "Kamida bitta fayl yuklang."

        # Validate phone number format
        if phone and not re.match(r'^\+\d{10,12}$', phone):
            form_errors['phone'] = "Telefon raqami noto‘g‘ri formatda (Masalan: +998123456789)."

        # Validate file types, count, and size
        max_size = 10 * 1024 * 1024  # 10MB
        if len(files) > 3:
            form_errors['files'] = "Maksimal 3 ta fayl yuklashingiz mumkin."
        for f in files:
            if f.size > max_size:
                form_errors['files'] = "Fayl hajmi 10MB dan kichik bo‘lishi kerak."
            mime_type, _ = mimetypes.guess_type(f.name)
            if mime_type not in ['application/pdf', 'application/msword',
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                form_errors['files'] = "Faqat PDF, DOC yoki DOCX fayllarni yuklash mumkin."

        if form_errors:
            messages.error(request, "Iltimos, barcha majburiy maydonlarni to‘g‘ri to‘ldiring.")
            return render(request, 'article_submission.html', {
                'fanlar': fanlar,
                'nashrlar': nashrlar,
                'form_data': request.POST,
                'form_errors': form_errors,
                'files': files
            })

        # Validate fan and ilm
        try:
            fan = FanTarmoq.objects.get(id=fan_id)
            ilm = IlmiyNashr.objects.get(id=ilm_id)
        except (FanTarmoq.DoesNotExist, IlmiyNashr.DoesNotExist):
            messages.error(request, "Tanlangan fan yoki nashr topilmadi.")
            return render(request, 'article_submission.html', {
                'fanlar': fanlar,
                'nashrlar': nashrlar,
                'form_data': request.POST,
                'form_errors': form_errors,
                'files': files
            })

        # Save submission
        try:
            submission = ArticleSubmission.objects.create(
                fan=fan,
                ilm=ilm,
                author=author,
                email=email,
                phone=phone,
                description=description
            )
        except Exception as e:
            print(f"Error creating ArticleSubmission: {str(e)}")
            messages.error(request, "Maqola saqlashda xatolik yuz berdi.")
            return render(request, 'article_submission.html', {
                'fanlar': fanlar,
                'nashrlar': nashrlar,
                'form_data': request.POST,
                'form_errors': form_errors,
                'files': files
            })

        # Save files
        saved_files = []
        for f in files:
            try:
                mime_type, _ = mimetypes.guess_type(f.name)
                file_obj = File.objects.create(
                    submission=submission,
                    file=f,
                    original_filename=f.name,
                    file_size=f.size,  # Set file_size from uploaded file
                    mime_type=mime_type or 'application/octet-stream',
                    file_type='pdf' if mime_type == 'application/pdf' else 'other',
                    uploaded_by=request.user if request.user.is_authenticated else None,
                    description=""
                )
                saved_files.append(file_obj)
            except Exception as e:
                print(f"Error creating File: {str(e)}")
                messages.error(request, "Fayl saqlashda xatolik yuz berdi.")
                submission.delete()  # Rollback submission if file save fails
                return render(request, 'article_submission.html', {
                    'fanlar': fanlar,
                    'nashrlar': nashrlar,
                    'form_data': request.POST,
                    'form_errors': form_errors,
                    'files': files
                })

        # Prepare Telegram message
        message = (
            f"<b>📥 Yangi maqola yuborildi</b>\n"
            f"<b>Muallif:</b> {author}\n"
            f"<b>Email:</b> {email}\n"
            f"<b>Telefon:</b> {phone}\n"
            f"<b>Fan:</b> {fan.name}\n"
            f"<b>Nashr:</b> {ilm.name}\n"
            f"<b>Izoh:</b> {description or '---'}\n"
            f"<b>Fayllar:</b> {', '.join([f.original_filename for f in saved_files])}"
        )

        # Send to Telegram (assuming send_to_telegram is defined)
        try:
            send_to_telegram(message, files=saved_files)
        except Exception as e:
            print(f"Error sending to Telegram: {str(e)}")
            messages.warning(request, "Maqola yuborildi, lekin Telegram xabari jo‘natilmadi.")

        messages.success(request, "Maqolalar muvaffaqiyatli yuborildi!")
        return redirect('article')

    return render(request, 'article_submission.html', {
        'fanlar': fanlar,
        'nashrlar': nashrlar
    })


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()

            subject = f"Imfakor Website Message from {contact_message.name}"
            message = (
                f"Name: {contact_message.name}\n"
                f"Email: {contact_message.email}\n"
                f"Subject: {contact_message.subject}\n\n"
                f"Message:\n{contact_message.message}"
            )
            admin_email = 'mmm857436@gmail.com'
            send_mail(subject, message, contact_message.email, [admin_email])

            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()

    context = {
        'form': form
    }
    return render(request, 'contact.html', context)


def test_diploma_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        journal_name = request.POST.get("journal_name")
        issue_number = request.POST.get("issue_number")
        article_url = request.POST.get("article_url")
        date_str = request.POST.get("date")

        email = request.POST.get("email")

        pub_date = None
        if date_str:
            try:
                pub_date = datetime.strptime(date_str, "%d-%m-%Y")
            except ValueError:
                pub_date = datetime.today()

        send_diploma_email(name, journal_name, issue_number, email, article_url, pub_date)
        return HttpResponse("Diploma sent successfully!")

    return render(request, "tt.html")


def sitemap_view(request):
    """Generate dynamic sitemap.xml"""
    from django.urls import reverse

    # Get all articles, journals, authors
    articles = Article.objects.filter(is_published=True).select_related('issue__journal')
    journals = Journal.objects.all()
    authors = Author.objects.all()

    context = {
        'articles': articles,
        'journals': journals,
        'authors': authors,
        'domain': request.get_host(),
        'protocol': 'https' if request.is_secure() else 'http',
    }
    return render(request, 'sitemap.xml', context, content_type='application/xml')


def robots_txt_view(request):
    """Generate robots.txt"""
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'

    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Sitemaps",
        f"Sitemap: {protocol}://{domain}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
