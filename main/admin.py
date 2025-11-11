# """
# Django Admin Configuration for Journal System
# This file registers all models with Django's built-in admin panel.
# Note: Currently, the project uses a custom admin panel. To enable Django's admin:
# 1. Uncomment line 25 in JournalSystem/urls.py: path('admin/', admin.site.urls),
# 2. Create a superuser: python manage.py createsuperuser
# 3. Access at /admin/
# """
#
# from django.contrib import admin
# from django.utils.html import format_html
# from .models import (
#     Navigation_For_Publishers_Page, Navigation_Item, FanTarmoq, IlmiyNashr,
#     ArticleSubmission, ContactMessage, Journal, JournalEditor, JournalPolicy,
#     Issue, Author, File, Article, ArticleAuthor, SiteSEO
# )
#
#
# # Customize Admin Site
# admin.site.site_header = "Imfaktor Admin Panel"
# admin.site.site_title = "Imfaktor Admin"
# admin.site.index_title = "Journal Management System"
#
#
# @admin.register(FanTarmoq)
# class FanTarmoqAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug', 'is_active', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('created_at', 'updated_at')
#
#
# @admin.register(IlmiyNashr)
# class IlmiyNashrAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug', 'is_active', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('created_at', 'updated_at')
#
#
# @admin.register(ArticleSubmission)
# class ArticleSubmissionAdmin(admin.ModelAdmin):
#     list_display = ('author', 'email', 'fan', 'ilm', 'submitted_at')
#     list_filter = ('fan', 'ilm', 'submitted_at')
#     search_fields = ('author', 'email', 'description')
#     readonly_fields = ('submitted_at',)
#     date_hierarchy = 'submitted_at'
#
#
# @admin.register(ContactMessage)
# class ContactMessageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'subject', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('name', 'email', 'subject', 'message')
#     readonly_fields = ('created_at',)
#     date_hierarchy = 'created_at'
#
#
# class JournalEditorInline(admin.TabularInline):
#     model = JournalEditor
#     extra = 0
#     fields = ('first_name', 'last_name', 'editor_type', 'affiliation', 'is_active')
#
#
# class JournalPolicyInline(admin.TabularInline):
#     model = JournalPolicy
#     extra = 0
#     fields = ('policy_type', 'title', 'is_active')
#
#
# @admin.register(Journal)
# class JournalAdmin(admin.ModelAdmin):
#     list_display = ('title', 'initials', 'is_active', 'is_open_access', 'created_at')
#     list_filter = ('is_active', 'is_open_access', 'created_at')
#     search_fields = ('title', 'initials', 'description', 'publisher')
#     prepopulated_fields = {'url_slug': ('title',)}
#     readonly_fields = ('created_at', 'updated_at')
#     inlines = [JournalEditorInline, JournalPolicyInline]
#
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('title', 'initials', 'abbreviation', 'url_slug', 'description')
#         }),
#         ('SEO Settings', {
#             'fields': ('meta_description', 'meta_keywords')
#         }),
#         ('Language & Locale', {
#             'fields': ('languages', 'primary_locale')
#         }),
#         ('Publication Details', {
#             'fields': ('publisher', 'issn_print', 'issn_online', 'is_open_access')
#         }),
#         ('Contact & Web', {
#             'fields': ('contact_email', 'website', 'cover_image')
#         }),
#         ('Status', {
#             'fields': ('is_active',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#
# @admin.register(JournalEditor)
# class JournalEditorAdmin(admin.ModelAdmin):
#     list_display = ('full_name', 'journal_id', 'editor_type', 'affiliation', 'is_active')
#     list_filter = ('editor_type', 'is_active')
#     search_fields = ('first_name', 'last_name', 'affiliation')
#     readonly_fields = ('created_at', 'updated_at')
#
#
# @admin.register(JournalPolicy)
# class JournalPolicyAdmin(admin.ModelAdmin):
#     list_display = ('title', 'journal_id', 'policy_type', 'is_active', 'updated_at')
#     list_filter = ('policy_type', 'is_active', 'updated_at')
#     search_fields = ('title', 'content')
#     readonly_fields = ('created_at', 'updated_at')
#
#
# class ArticleAuthorInline(admin.TabularInline):
#     model = ArticleAuthor
#     extra = 1
#     autocomplete_fields = ['author']
#
#
# @admin.register(Issue)
# class IssueAdmin(admin.ModelAdmin):
#     list_display = ('display_name', 'journal', 'volume', 'number', 'is_published', 'is_active', 'publication_date')
#     list_filter = ('is_published', 'is_active', 'journal', 'publication_date')
#     search_fields = ('volume', 'number', 'description')
#     readonly_fields = ('created_at', 'updated_at')
#     date_hierarchy = 'publication_date'
#
#     def display_name(self, obj):
#         return f"{obj.journal.initials} Vol.{obj.volume} No.{obj.number}"
#     display_name.short_description = 'Issue'
#
#
# @admin.register(Author)
# class AuthorAdmin(admin.ModelAdmin):
#     list_display = ('full_name', 'email', 'affiliation', 'orcid', 'is_active')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('first_name', 'middle_name', 'last_name', 'email', 'affiliation', 'orcid')
#     readonly_fields = ('created_at', 'updated_at', 'article_count')
#
#     fieldsets = (
#         ('Personal Information', {
#             'fields': ('first_name', 'middle_name', 'last_name', 'photo')
#         }),
#         ('Contact & Professional', {
#             'fields': ('email', 'affiliation', 'orcid', 'bio')
#         }),
#         ('Social Media', {
#             'fields': ('website', 'google_scholar', 'researchgate', 'linkedin'),
#             'classes': ('collapse',)
#         }),
#         ('Status', {
#             'fields': ('is_active',)
#         }),
#         ('Statistics', {
#             'fields': ('article_count',),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def full_name(self, obj):
#         return obj.full_name
#     full_name.short_description = 'Name'
#
#
# @admin.register(File)
# class FileAdmin(admin.ModelAdmin):
#     list_display = ('article', 'file_type', 'file', 'uploaded_at')
#     list_filter = ('file_type', 'uploaded_at')
#     search_fields = ('article__title',)
#     readonly_fields = ('uploaded_at', 'updated_at')
#
#
# @admin.register(Article)
# class ArticleAdmin(admin.ModelAdmin):
#     list_display = ('title', 'issue', 'is_published', 'featured', 'open_access', 'date_published', 'views')
#     list_filter = ('is_published', 'featured', 'open_access', 'language', 'date_published')
#     search_fields = ('title', 'subtitle', 'abstract', 'keywords', 'doi')
#     readonly_fields = ('created_at', 'updated_at', 'views')
#     date_hierarchy = 'date_published'
#     inlines = [ArticleAuthorInline]
#     autocomplete_fields = ['issue']
#
#     fieldsets = (
#         ('Article Information', {
#             'fields': ('title', 'subtitle', 'abstract', 'keywords', 'language')
#         }),
#         ('Publication Details', {
#             'fields': ('issue', 'date_published', 'first_page', 'last_page')
#         }),
#         ('SEO & Identifiers', {
#             'fields': ('meta_description', 'doi', 'slug')
#         }),
#         ('Content', {
#             'fields': ('references',),
#             'classes': ('collapse',)
#         }),
#         ('Files', {
#             'description': 'Main PDF file for the article',
#             'fields': ('main_pdf',),
#         }),
#         ('Status & Features', {
#             'fields': ('is_published', 'featured', 'open_access')
#         }),
#         ('Statistics', {
#             'fields': ('views',),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#
# @admin.register(ArticleAuthor)
# class ArticleAuthorAdmin(admin.ModelAdmin):
#     list_display = ('article', 'author', 'order', 'is_corresponding')
#     list_filter = ('is_corresponding',)
#     search_fields = ('article__title', 'author__first_name', 'author__last_name')
#     autocomplete_fields = ['article', 'author']
#
#
# @admin.register(Navigation_For_Publishers_Page)
# class NavigationForPublishersPageAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)
#
#
# @admin.register(Navigation_Item)
# class NavigationItemAdmin(admin.ModelAdmin):
#     list_display = ('navigation', 'text_preview')
#     search_fields = ('text',)
#
#     def text_preview(self, obj):
#         return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
#     text_preview.short_description = 'Text'
#
#
# @admin.register(SiteSEO)
# class SiteSEOAdmin(admin.ModelAdmin):
#     list_display = ('meta_title', 'enable_google_scholar', 'auto_sitemap')
#
#     fieldsets = (
#         ('Meta Tags', {
#             'fields': ('meta_title', 'meta_description', 'meta_keywords')
#         }),
#         ('Publisher Information', {
#             'fields': ('publisher_name',)
#         }),
#         ('Indexing Settings', {
#             'fields': ('enable_google_scholar', 'auto_sitemap')
#         }),
#     )
#
#     def has_add_permission(self, request):
#         # Only allow one SiteSEO instance
#         return not SiteSEO.objects.exists()
#
#     def has_delete_permission(self, request, obj=None):
#         # Prevent deletion of SEO settings
#         return False
