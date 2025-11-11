# Admin Panel Guide

## Overview

This project has **TWO admin panel options**:

1. **Custom Admin Panel** (Currently Active) - `/admin/`
2. **Django Built-in Admin** (Available but disabled) - Can be enabled

---

## 1. Custom Admin Panel (Currently Active)

### Access
- **URL**: `http://yourdomain.com/admin/`
- **Login**: `/admin/login/`
- **Credentials**: Configured in `main/config.py`

### Features

#### Journal Management
- Create, edit, delete journals
- Manage journal settings (ISSN, publisher, cover image)
- Configure journal editors and policies
- Export journal data to CSV

#### Article Management
- Add articles with multiple authors
- Upload PDF files
- Set publication status (draft/published)
- Featured article toggle
- Bulk operations support
- Export articles to CSV

#### Issue Management
- Create journal issues (volume, number)
- Set publication dates
- Mark issues as active/published
- Manage issue cover images

#### Author Management
- Full CRUD operations
- Author profiles with photos
- ORCID integration
- Social media links (Google Scholar, ResearchGate, LinkedIn)
- Export authors to CSV
- Email functionality to contact authors

#### Editor Management (Per Journal)
- Add/remove journal editors
- Editor types: Chief, Deputy, Section, Associate, Technical, Guest
- Editor profiles with photos and affiliations
- Export editors to CSV

#### Policy Management (Per Journal)
- Submission guidelines
- Review process
- Publication policy
- Ethics guidelines
- Copyright policy
- Open access policy
- Plagiarism policy
- Retraction policy
- Editorial policy

#### SEO Management
- Site-wide SEO settings
- Meta tags configuration
- Google Scholar indexing toggle
- Auto-sitemap generation
- Manual sitemap/robots.txt update triggers

### Admin Endpoints (120 total)

**Authentication:**
- `/admin/login/` - Admin login
- `/admin/logout/` - Admin logout

**Dashboard:**
- `/admin/` - Main dashboard

**Journals:**
- `/admin/journals/list/` - List all journals
- `/admin/journals/add/` - Add new journal
- `/admin/journals/update/<id>/` - Update journal
- `/admin/journals/delete/<id>/` - Delete journal
- `/admin/journals/<id>/manage/` - Journal management page
- `/admin/journals/<id>/settings/` - Journal settings

**Articles:**
- `/admin/articles/delete/<id>/` - Delete article
- `/admin/articles/update/<id>/` - Update article
- `/admin/articles/toggle-featured/<id>/` - Toggle featured status
- `/admin/export/articles/` - Export articles CSV

**Issues:**
- `/admin/issues/list/` - List issues
- `/admin/issues/add/` - Add issue
- `/admin/issues/update/<id>/` - Update issue
- `/admin/issues/delete/<id>/` - Delete issue

**Authors:**
- `/admin/authors/` - Authors management page
- `/admin/authors/list/` - List authors (AJAX)
- `/admin/authors/add/` - Add author
- `/admin/authors/update/<id>/` - Update author
- `/admin/authors/delete/<id>/` - Delete author
- `/admin/authors/details/<id>/` - Author details
- `/admin/export/authors/` - Export authors CSV
- `/admin/message-authors/` - Email all authors
- `/admin/message-authors/<id>/` - Email specific author

**Editors:**
- `/admin/journals/<id>/editors/` - List editors
- `/admin/journals/<id>/editors/add/` - Add editor
- `/admin/journals/<id>/editors/<id>/update/` - Update editor
- `/admin/journals/<id>/editors/<id>/delete/` - Delete editor
- `/admin/journals/<id>/export/editors/` - Export editors CSV

**Policies:**
- `/admin/journals/<id>/policies/` - List policies
- `/admin/journals/<id>/policies/add/` - Add policy
- `/admin/journals/<id>/policies/<id>/update/` - Update policy
- `/admin/journals/<id>/policies/<id>/delete/` - Delete policy
- `/admin/journals/<id>/export/policies/` - Export policies CSV

**SEO:**
- `/admin/seo/` - SEO settings page
- `/admin/seo/status/` - Get SEO status
- `/admin/seo/save/` - Save SEO settings
- `/admin/seo/update-sitemap/` - Manually update sitemap
- `/admin/seo/update-robots/` - Manually update robots.txt

**FanTarmoq & IlmiyNashr:**
- `/admin/fan-tarmoq/list/` - List scientific fields
- `/admin/fan-tarmoq/add/` - Add scientific field
- `/admin/fan-tarmoq/<id>/edit/` - Edit scientific field
- `/admin/fan-tarmoq/<id>/delete/` - Delete scientific field
- `/admin/ilmiy-nashr/list/` - List publication types
- `/admin/ilmiy-nashr/add/` - Add publication type
- `/admin/ilmiy-nashr/<id>/edit/` - Edit publication type
- `/admin/ilmiy-nashr/<id>/delete/` - Delete publication type

**Navigation:**
- `/admin/navigation-publishers/` - Navigation management
- `/admin/navigation/list/` - List navigation items
- `/admin/navigation/add/` - Add navigation item
- `/admin/navigation/update/<id>/` - Update navigation
- `/admin/navigation/delete/<id>/` - Delete navigation

### Custom Admin Security Notes

⚠️ **Current Implementation Issues** (See SECURITY.md):
- Uses hardcoded credentials in config.py
- Custom authentication instead of Django User model
- Session-based with configurable expiry
- No rate limiting on login attempts
- No password hashing (plaintext comparison)

**Recommendations:**
1. Migrate to Django User model with proper password hashing
2. Implement rate limiting (django-ratelimit)
3. Add 2FA support
4. Use environment variables for credentials
5. Implement audit logging

---

## 2. Django Built-in Admin (Available)

### How to Enable

**Step 1:** Uncomment line 25 in `JournalSystem/urls.py`:
```python
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),  # Uncomment this line
    # ... other paths
]
```

**Step 2:** Create a superuser:
```bash
python manage.py createsuperuser
```

**Step 3:** Access Django admin:
```
http://yourdomain.com/admin/
```

### Features

All models are now registered in `main/admin.py` with:
- ✅ List display with important fields
- ✅ Search functionality
- ✅ Filters
- ✅ Inline editing for related models
- ✅ Fieldsets for organized forms
- ✅ Readonly fields for timestamps
- ✅ Autocomplete for foreign keys
- ✅ Custom methods for better display

**Registered Models:**
- FanTarmoq (Scientific Fields)
- IlmiyNashr (Publication Types)
- ArticleSubmission
- ContactMessage
- Journal (with Editor & Policy inlines)
- JournalEditor
- JournalPolicy
- Issue
- Author
- File
- Article (with ArticleAuthor inline)
- ArticleAuthor
- Navigation_For_Publishers_Page
- Navigation_Item
- SiteSEO

**Advantages:**
- Built-in security (password hashing, CSRF protection)
- User permissions and groups
- Action logging
- Better UX/UI
- Mobile responsive
- No custom code to maintain

---

## SEO Features (Both Admin Panels)

### Sitemap.xml

**Access:** `http://yourdomain.com/sitemap.xml`

**Includes:**
- Homepage
- Static pages (About, Contact, For Publishers, Send Article)
- All journals
- All published issues (NEW - just added!)
- All published articles
- All active authors

**Features:**
- Dynamic generation
- Proper lastmod dates
- Priority and changefreq settings
- Optimized for Google Scholar

### Robots.txt

**Access:** `http://yourdomain.com/robots.txt`

**Features:**
- Dynamic generation based on SiteSEO settings
- Sitemap URL included
- Admin/API areas blocked
- Google Scholar support toggle

**Configuration:**
If `SiteSEO.enable_google_scholar = True`:
- Allows crawling of /articles/, /journals/, /authors/, /issues/
- Disallows /admin/, /api/

If `SiteSEO.enable_google_scholar = False`:
- Limited indexing enabled

---

## Recent Improvements (November 11, 2025)

### 1. URL Routing Enhancement
- **Changed:** Switched from basic sitemap/robots.txt to advanced versions
- **File:** `main/urls.py`
- **Benefit:** Now uses `admin_views.generate_sitemap()` and `admin_views.robots_txt()` which include:
  - Issues in sitemap
  - SiteSEO model integration
  - Error handling
  - Statistics tracking

### 2. Sitemap Template Enhancement
- **Added:** Issues section to sitemap.xml
- **Removed:** Unused XML namespaces (news, xhtml, mobile, image, video)
- **File:** `templates/sitemap.xml`
- **Benefit:** Better SEO, cleaner XML, faster parsing

### 3. Django Admin Registration
- **Created:** `main/admin.py` (265 lines)
- **Registered:** All 15 models with full configuration
- **Features:**
  - Inline editing for related models (editors, policies, article authors)
  - Search and filter capabilities
  - Custom fieldsets
  - Readonly fields for timestamps
  - Autocomplete for foreign keys
  - Custom display methods

---

## Recommendations

### For Development
✅ Use Custom Admin Panel (current setup)
- Fast and functional
- Already integrated
- No additional setup needed

### For Production
✅ Consider migrating to Django Admin:
- Better security out of the box
- User management
- Permissions system
- Audit logging
- Better UX
- Mobile responsive
- Community support

### Security Priority
⚠️ **HIGH PRIORITY** - Address custom admin security issues:
1. Replace hardcoded credentials with Django User model
2. Implement proper password hashing
3. Add rate limiting
4. Enable HTTPS/SSL
5. Implement audit logging

---

## Testing

### Test Sitemap
```bash
curl http://localhost:8000/sitemap.xml
```

### Test Robots.txt
```bash
curl http://localhost:8000/robots.txt
```

### Test Custom Admin
1. Navigate to http://localhost:8000/admin/login/
2. Enter credentials from `main/config.py`
3. Access dashboard

### Test Django Admin (if enabled)
1. Create superuser: `python manage.py createsuperuser`
2. Navigate to http://localhost:8000/admin/
3. Login with superuser credentials

---

## Troubleshooting

### Custom Admin Login Fails
- Check `main/config.py` for correct credentials
- Verify session configuration in `settings.py`
- Check SESSION_EXPIRY environment variable

### Sitemap Empty or Error
- Check if SiteSEO model has an instance
- Verify articles are marked `is_published=True`
- Check server logs for errors

### Django Admin Not Accessible
- Ensure URL is uncommented in `urls.py`
- Run migrations: `python manage.py migrate`
- Create superuser if not exists

---

## Support

For issues or questions:
- Check `SECURITY.md` for security-related items
- Check `DEPLOYMENT.md` for production setup
- Check server logs for detailed error messages
