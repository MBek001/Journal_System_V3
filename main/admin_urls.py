# admin_urls.py - Corrected Version
from django.urls import path
from main import admin_views, admin_journal, admin_email_sending

urlpatterns = [
    path('admin/login/', admin_views.admin_login, name='admin_login'),
    path('admin/logout/', admin_views.admin_logout, name='admin_logout'),

    # Admin Dashboard
    path('admin/', admin_views.admin_dashboard, name='custom_admin'),
    path('admin/message-authors/', admin_email_sending.message_authors_view, name='message_authors'),
    path('admin/message-authors/<int:author_id>/', admin_email_sending.message_authors_view,
         name='message_author_single'),

    # Add these URL patterns to your admin URLs
    path('admin/journals/<int:journal_id>/manage/', admin_views.journal_management_page,
         name='journal_management_page'),
    path('admin/journals/<int:journal_id>/issues/', admin_views.journal_issues_ajax, name='journal_issues_ajax'),
    path('admin/journals/<int:journal_id>/articles/', admin_views.journal_articles_ajax, name='journal_articles_ajax'),
    path('admin/journals/<int:journal_id>/issues/add/', admin_views.journal_add_issue_ajax,
         name='journal_add_issue_ajax'),
    path('admin/journals/<int:journal_id>/articles/add/', admin_journal.journal_add_article_ajax,
         name='journal_add_article_ajax'),
    path('admin/journals/<int:journal_id>/settings/', admin_views.journal_settings_ajax, name='journal_settings_ajax'),

    # Article Management
    path('admin/articles/delete/<int:article_id>/', admin_views.delete_article_ajax, name='admin_delete_article'),
    path('admin/articles/update/<int:article_id>/', admin_journal.update_article_ajax, name='admin_update_article'),
    path('admin/articles/toggle-featured/<int:article_id>/', admin_views.toggle_article_featured,
         name='admin_toggle_featured'),

    # Journal Management
    path('admin/journals/add/', admin_views.add_journal_ajax, name='admin_add_journal'),
    path('admin/journals/list/', admin_views.journals_list_ajax, name='admin_journals_list'),
    path('admin/journals/delete/<int:journal_id>/', admin_views.delete_journal_ajax, name='admin_delete_journal'),
    path('admin/journals/update/<int:journal_id>/', admin_views.update_journal_ajax, name='admin_update_journal'),
    path('admin/journals/<int:journal_id>/issues/', admin_views.get_journal_issues, name='admin_journal_issues'),

    # Journal Editors Management URLs
    path('admin/journals/<int:journal_id>/editors/', admin_journal.journal_editors_ajax, name='journal_editors_ajax'),
    path('admin/journals/<int:journal_id>/editors/add/', admin_journal.journal_add_editor_ajax,
         name='journal_add_editor_ajax'),
    path('admin/journals/<int:journal_id>/editors/<int:editor_id>/update/', admin_journal.journal_update_editor_ajax,
         name='journal_update_editor_ajax'),
    path('admin/journals/<int:journal_id>/editors/<int:editor_id>/delete/', admin_journal.journal_delete_editor_ajax,
         name='journal_delete_editor_ajax'),

    # Journal Policies Management URLs
    path('admin/journals/<int:journal_id>/policies/', admin_journal.journal_policies_ajax,
         name='journal_policies_ajax'),
    path('admin/journals/<int:journal_id>/policies/add/', admin_journal.journal_add_policy_ajax,
         name='journal_add_policy_ajax'),
    path('admin/journals/<int:journal_id>/policies/<int:policy_id>/update/', admin_journal.journal_update_policy_ajax,
         name='journal_update_policy_ajax'),
    path('admin/journals/<int:journal_id>/policies/<int:policy_id>/delete/', admin_journal.journal_delete_policy_ajax,
         name='journal_delete_policy_ajax'),

    # Utility URLs
    path('admin/editor-types/', admin_journal.get_editor_types, name='get_editor_types'),
    path('admin/policy-types/', admin_journal.get_policy_types, name='get_policy_types'),

    # Export URLs
    path('admin/journals/<int:journal_id>/export/editors/', admin_journal.export_journal_editors_csv,
         name='export_journal_editors'),
    path('admin/journals/<int:journal_id>/export/policies/', admin_journal.export_journal_policies_csv,
         name='export_journal_policies'),

    # Issue Management
    path('admin/issues/add/', admin_views.add_issue_ajax, name='admin_add_issue'),
    path('admin/issues/list/', admin_views.issues_list_ajax, name='admin_issues_list'),
    path('admin/issues/update/<int:issue_id>/', admin_views.update_issue_ajax, name='admin_update_issue'),
    path('admin/issues/delete/<int:issue_id>/', admin_views.delete_issue_ajax, name='admin_delete_issue'),

    # Author Management
    path('admin/authors/', admin_views.authors_list_ajax, name='admin_authors_list_page'),
    path('admin/authors/list/', admin_views.authors_list_ajax, name='admin_authors_list'),
    path('admin/authors/add/', admin_views.add_author_ajax, name='admin_add_author'),
    path('admin/authors/update/<int:author_id>/', admin_views.update_author_ajax, name='admin_update_author'),
    path('admin/authors/delete/<int:author_id>/', admin_views.delete_author_ajax, name='admin_delete_author'),
    path('admin/authors/details/<int:author_id>/', admin_views.author_details_ajax, name='admin_author_details'),
    path('admin/export/authors/', admin_views.export_authors_csv, name='admin_export_authors'),

    # FanTarmoq & IlmiyNashr Management
    path('admin/fan-tarmoq/list/', admin_views.fan_tarmoq_list_ajax, name='admin_fan_tarmoq_list'),
    path('admin/fan-tarmoq/add/', admin_views.add_fan_tarmoq_ajax, name='admin_add_fan_tarmoq'),
    path('admin/fan-tarmoq/<int:fan_tarmoq_id>/edit/', admin_views.edit_fan_tarmoq_ajax, name='admin_edit_fan_tarmoq'),
    path('admin/fan-tarmoq/<int:fan_tarmoq_id>/delete/', admin_views.delete_fan_tarmoq_ajax,
         name='admin_delete_fan_tarmoq'),

    path('admin/ilmiy-nashr/list/', admin_views.ilmiy_nashr_list_ajax, name='admin_ilmiy_nashr_list'),
    path('admin/ilmiy-nashr/add/', admin_views.add_ilmiy_nashr_ajax, name='admin_add_ilmiy_nashr'),
    path('admin/ilmiy-nashr/<int:ilmiy_nashr_id>/edit/', admin_views.edit_ilmiy_nashr_ajax,
         name='admin_edit_ilmiy_nashr'),
    path('admin/ilmiy-nashr/<int:ilmiy_nashr_id>/delete/', admin_views.delete_ilmiy_nashr_ajax,
         name='admin_delete_ilmiy_nashr'),

    # SEO & Utility
    path('admin/seo/', admin_views.load_seo, name='admin_load_seo'),
    path('admin/seo/status/', admin_views.get_seo_status, name='admin_load_seo_status'),
    path('admin/seo/save/', admin_views.save_seo_settings, name='admin_save_seo'),
    path('admin/export/articles/', admin_views.export_articles_csv, name='admin_export_articles'),

    # Navigation for Publishers Management
    path('admin/navigation-publishers/', admin_views.navigation_publishers_page,
         name='admin_navigation_publishers_page'),
    path('admin/navigation/list/', admin_views.navigation_list_ajax, name='admin_navigation_list'),
    path('admin/navigation/add/', admin_views.add_navigation_ajax, name='admin_add_navigation'),
    path('admin/navigation/update/<int:navigation_id>/', admin_views.update_navigation_ajax,
         name='admin_update_navigation'),
    path('admin/navigation/delete/<int:navigation_id>/', admin_views.delete_navigation_ajax,
         name='admin_delete_navigation'),

    # Public (No Login)
    path('sitemap.xml', admin_views.generate_sitemap, name='sitemap'),
    path('robots.txt', admin_views.robots_txt, name='robots_txt'),
    path('admin/seo/status/', admin_views.get_seo_status, name='admin_seo_status'),
    path('admin/seo/update-sitemap/', admin_views.update_sitemap_manual, name='admin_update_sitemap'),
    path('admin/seo/update-robots/', admin_views.update_robots_manual, name='admin_update_robots'),

]
