# Multilingual Quick Start Guide
## Get Started in 30 Minutes!

This is a condensed version to get you started quickly. For full details, see [MULTILINGUAL_GUIDE.md](MULTILINGUAL_GUIDE.md).

---

## Quick Setup (5 Steps)

### Step 1: Update Settings (5 minutes)

Add to `JournalSystem/settings.py`:

```python
# After BASE_DIR definition
from django.utils.translation import gettext_lazy as _

# Find and update these settings:
LANGUAGE_CODE = 'uz'

LANGUAGES = [
    ('uz', _('O\'zbekcha')),
    ('ru', _('Русский')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

USE_I18N = True
USE_L10N = True

# Update MIDDLEWARE - add after SessionMiddleware:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ADD THIS LINE
    'django.middleware.common.CommonMiddleware',
    # ... rest stays the same
]
```

### Step 2: Update URLs (5 minutes)

Replace `JournalSystem/urls.py` with:

```python
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import path, include
from JournalSystem import settings

# Non-translatable URLs
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Translatable URLs
urlpatterns += i18n_patterns(
    path('', include("main.urls")),
    path('', include("main.admin_urls")),
    path('', include("main.article_url")),
    prefix_default_language=False,
)
```

### Step 3: Create Language Switcher (5 minutes)

Create `templates/language_switcher.html`:

```django
{% load i18n %}

<div class="language-switcher">
    <form action="{% url 'set_language' %}" method="post" class="language-form">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <select name="language" onchange="this.form.submit()" class="language-select">
            {% get_current_language as LANGUAGE_CODE %}
            {% get_available_languages as LANGUAGES %}
            {% for lang_code, lang_name in LANGUAGES %}
                <option value="{{ lang_code }}" {% if lang_code == LANGUAGE_CODE %}selected{% endif %}>
                    {% if lang_code == 'uz' %}🇺🇿 O'zbekcha
                    {% elif lang_code == 'ru' %}🇷🇺 Русский
                    {% elif lang_code == 'en' %}🇬🇧 English
                    {% endif %}
                </option>
            {% endfor %}
        </select>
    </form>
</div>
```

Add CSS to `static/css/style.css`:

```css
/* Language Switcher */
.language-switcher {
    margin-left: auto;
    padding: 0 12px;
}

.language-select {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    cursor: pointer;
    min-width: 140px;
}

.language-select:hover {
    border-color: #0056b3;
}

.language-select:focus {
    outline: none;
    border-color: #0056b3;
    box-shadow: 0 0 0 3px rgba(0, 86, 179, 0.1);
}

@media (max-width: 768px) {
    .language-switcher {
        padding: 8px;
        order: -1; /* Show before hamburger menu */
    }
    .language-select {
        width: 100%;
    }
}
```

### Step 4: Update Base Template (10 minutes)

Update `templates/base.html`:

```django
{% load static %}
{% load i18n %}  <!-- ADD THIS LINE at the top -->
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <!-- ... existing head content ... -->
</head>
<body>

<header class="journal-header">
    <div class="container">
        <div class="d-flex flex-wrap align-items-center">
            <!-- Logo -->
            <a href="{% url 'home' %}" class="journal-logo-container">
                <img src="{% static 'images/logocha.png' %}" alt="Imfaktor Logo">
                <span class="journal-logo-text">IMFAKTOR</span>
            </a>

            <!-- Desktop Navigation -->
            <div class="d-none d-lg-flex justify-content-center flex-grow-1">
                <ul class="d-flex list-unstyled mb-0">
                    <li class="mx-2">
                        <a href="{% url 'home' %}" class="nav-link">{% trans "Bosh sahifa" %}</a>
                    </li>
                    <li class="mx-2">
                        <a href="{% url 'journals' %}" class="nav-link">{% trans "Jurnallar" %}</a>
                    </li>
                    <li class="mx-2">
                        <a href="{% url 'allauthors' %}" class="nav-link">{% trans "Mualliflar" %}</a>
                    </li>
                    <li class="mx-2">
                        <a href="{% url 'articles_list' %}" class="nav-link">{% trans "Maqolalar" %}</a>
                    </li>
                    <li class="mx-2">
                        <a href="{% url 'article' %}" class="nav-link">{% trans "Maqola yuborish" %}</a>
                    </li>
                    <li class="mx-2">
                        <a href="{% url 'admin_login' %}" class="nav-link">{% trans "Login" %}</a>
                    </li>
                </ul>
            </div>

            <!-- Language Switcher - ADD THIS -->
            {% include 'language_switcher.html' %}

            <!-- Mobile menu button -->
            <button class="d-lg-none mobile-menu-btn" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <i class="fas fa-bars"></i>
            </button>

            <!-- Mobile navigation -->
            <div class="collapse navbar-collapse d-lg-none w-100" id="navbarNav">
                <ul class="navbar-nav flex-column mt-3">
                    <li class="nav-item">
                        <a href="{% url 'home' %}" class="nav-link">{% trans "Bosh sahifa" %}</a>
                    </li>
                    <li class="nav-item">
                        <a href="{% url 'journals' %}" class="nav-link">{% trans "Jurnallar" %}</a>
                    </li>
                    <li class="nav-item">
                        <a href="{% url 'allauthors' %}" class="nav-link">{% trans "Mualliflar" %}</a>
                    </li>
                    <li class="nav-item">
                        <a href="{% url 'articles_list' %}" class="nav-link">{% trans "Maqolalar" %}</a>
                    </li>
                    <li class="nav-item">
                        <a href="{% url 'admin_login' %}" class="nav-link">{% trans "Login" %}</a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</header>

<!-- Rest of template stays the same -->
```

### Step 5: Create Translation Files (5 minutes)

Run these commands:

```bash
# Create locale directories
mkdir -p locale/uz/LC_MESSAGES
mkdir -p locale/ru/LC_MESSAGES
mkdir -p locale/en/LC_MESSAGES

# Generate translation files
python manage.py makemessages -l ru
python manage.py makemessages -l en

# This creates:
# locale/ru/LC_MESSAGES/django.po
# locale/en/LC_MESSAGES/django.po
```

---

## Test It!

1. **Start server:**
   ```bash
   python manage.py runserver
   ```

2. **Test URLs:**
   - Uzbek: `http://localhost:8000/`
   - Russian: `http://localhost:8000/ru/`
   - English: `http://localhost:8000/en/`

3. **Test language switcher:**
   - Click dropdown in header
   - Select different language
   - Page should reload in new language

---

## Translate Content

### Edit Translation Files:

Open `locale/ru/LC_MESSAGES/django.po`:

```po
msgid "Bosh sahifa"
msgstr "Главная страница"

msgid "Jurnallar"
msgstr "Журналы"

msgid "Mualliflar"
msgstr "Авторы"

msgid "Maqolalar"
msgstr "Статьи"

msgid "Maqola yuborish"
msgstr "Отправить статью"

msgid "Login"
msgstr "Войти"
```

Open `locale/en/LC_MESSAGES/django.po`:

```po
msgid "Bosh sahifa"
msgstr "Home"

msgid "Jurnallar"
msgstr "Journals"

msgid "Mualliflar"
msgstr "Authors"

msgid "Maqolalar"
msgstr "Articles"

msgid "Maqola yuborish"
msgstr "Submit Article"

msgid "Login"
msgstr "Login"
```

### Compile Translations:

```bash
python manage.py compilemessages
```

### Reload Browser - Translations Active! 🎉

---

## Add More Pages

For each template, add:

```django
{% load i18n %}

<!-- Wrap all text with {% trans %} -->
<h1>{% trans "Your text here" %}</h1>
<p>{% trans "Another text" %}</p>

<!-- For text with variables: -->
{% blocktrans with name=user.name %}
    Hello {{ name }}!
{% endblocktrans %}
```

Then run:

```bash
python manage.py makemessages -a  # Update all .po files
python manage.py compilemessages  # Compile
```

---

## Common Translations

Here are common phrases you'll need:

**Navigation:**
- Bosh sahifa → Главная страница → Home
- Jurnallar → Журналы → Journals
- Maqolalar → Статьи → Articles
- Mualliflar → Авторы → Authors
- Qidiruv → Поиск → Search
- Bog'lanish → Контакты → Contact

**Actions:**
- Ko'rish → Смотреть → View
- Yuklab olish → Скачать → Download
- O'qish → Читать → Read
- Yuborish → Отправить → Submit
- Saqlash → Сохранить → Save
- Bekor qilish → Отменить → Cancel

**Forms:**
- Ism → Имя → Name
- Email → Email → Email
- Xabar → Сообщение → Message
- Yuborish → Отправить → Submit
- Talab qilinadi → Обязательно → Required

**Status:**
- Yangi → Новый → New
- Nashr etilgan → Опубликовано → Published
- Kutilmoqda → Ожидается → Pending
- Rad etilgan → Отклонено → Rejected

---

## Pro Tips

### 1. Use Translation Tool (Rosetta)

```bash
pip install django-rosetta

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'rosetta',
]

# Add to urls.py
path('rosetta/', include('rosetta.urls')),

# Access at: http://localhost:8000/rosetta/
```

This gives you a web interface for editing translations!

### 2. Translate Incrementally

Don't try to translate everything at once:

**Week 1:** Navigation + Home page
**Week 2:** About + Contact pages
**Week 3:** Journals + Articles pages
**Week 4:** Forms + Error messages
**Week 5:** Database content

### 3. Use Google Translate for First Draft

```bash
# Install
pip install googletrans==4.0.0-rc1

# Create helper script
python translate_helper.py
```

Then manually review and fix translations.

### 4. Keep a Translation Glossary

Create `TRANSLATIONS.xlsx`:

| Uzbek | Russian | English |
|-------|---------|---------|
| Jurnal | Журнал | Journal |
| Maqola | Статья | Article |
| Muallif | Автор | Author |
| Nashr | Публикация | Publication |

---

## Troubleshooting

### Issue: Translations not showing

**Solution:**
```bash
python manage.py compilemessages
# Restart server
```

### Issue: Language switcher not working

**Check:**
1. Is `django.middleware.locale.LocaleMiddleware` in MIDDLEWARE?
2. Is it after SessionMiddleware?
3. Did you add `path('i18n/', include('django.conf.urls.i18n'))`?

### Issue: 404 on /ru/ or /en/

**Check:**
1. Are URLs wrapped in `i18n_patterns()`?
2. Restart server after changing urls.py

### Issue: Some text not translating

**Check:**
1. Did you add `{% load i18n %}` at top of template?
2. Is text wrapped in `{% trans "..." %}`?
3. Did you run `makemessages` and `compilemessages`?

---

## Next Steps

1. ✅ **Basic setup done** - Language switcher working
2. 🔄 **Translate templates** - Add {% trans %} to all pages
3. 🔄 **Translate .po files** - Add Russian/English translations
4. 🔄 **Database content** - Use Django Parler for articles/journals
5. 🔄 **Test thoroughly** - All pages, all languages
6. 🔄 **Deploy** - Production

---

## Need Help?

Commands cheat sheet:

```bash
# Create/update translation files
python manage.py makemessages -l ru
python manage.py makemessages -l en
python manage.py makemessages -a  # All languages

# Compile translations
python manage.py compilemessages

# Check which strings need translation
python manage.py makemessages --check-only
```

---

**You're now ready to make your site multilingual!** 🌍

For more details, see the complete [MULTILINGUAL_GUIDE.md](MULTILINGUAL_GUIDE.md).
