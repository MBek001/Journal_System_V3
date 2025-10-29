from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Navigation_For_Publishers_Page(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Navigation_Item(models.Model):
    navigation = models.ForeignKey(Navigation_For_Publishers_Page, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text


class TimeStampedModel(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FanTarmoq(TimeStampedModel):
    """Scientific field/discipline model"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Field Name")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Description of this scientific field")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Fan Tarmoq"
        verbose_name_plural = "Fan Tarmoqlari"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class IlmiyNashr(TimeStampedModel):
    """Scientific publication type model"""
    name = models.CharField(max_length=150, unique=True, verbose_name="Publication Type")
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ilmiy Nashr"
        verbose_name_plural = "Ilmiy Nashrlar"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ArticleSubmission(models.Model):
    fan = models.ForeignKey(FanTarmoq, on_delete=models.CASCADE)
    ilm = models.ForeignKey(IlmiyNashr, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    description = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} - {self.fan.name}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class Journal(TimeStampedModel):
    title = models.CharField(max_length=255, unique=True)
    initials = models.CharField(max_length=20, help_text="Journal initials/acronym")
    abbreviation = models.CharField(max_length=50, blank=True)
    url_slug = models.SlugField(max_length=100, unique=True)

    description = models.TextField(help_text="Journal description and scope")
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description (max 160 chars)"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO keywords separated by commas"
    )

    languages = models.JSONField(default=list, help_text="Supported languages ['en', 'uz', 'ru']")
    primary_locale = models.CharField(max_length=20, default='en')

    is_active = models.BooleanField(default=True)
    is_open_access = models.BooleanField(default=True)

    publisher = models.CharField(max_length=200, blank=True)
    issn_print = models.CharField(
        max_length=20,
        blank=True,
        help_text="Print ISSN (format: XXXX-XXXX)"
    )
    issn_online = models.CharField(
        max_length=20,
        blank=True,
        help_text="Online ISSN (format: XXXX-XXXX)"
    )

    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    cover_image = models.ImageField(
        upload_to='journal_covers/',
        blank=True,
        null=True,
        help_text="Journal cover image"
    )

    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journals"
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.url_slug:
            self.url_slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('journal_detail', kwargs={'journal_slug': self.url_slug})

    @property
    def current_issue(self):
        """Get the current active published issue"""
        return self.issues.filter(is_active=True, is_published=True).first()


class JournalEditor(models.Model):
    EDITOR_TYPES = [
        ('chief', 'Bosh muharrir'),
        ('deputy', 'Muharrir o\'rinbosari'),
        ('section', 'Bo\'lim muharriri'),
        ('associate', 'Yordamchi muharrir'),
        ('technical', 'Texnik muharrir'),
        ('guest', 'Mehmon muharrir'),
    ]

    id = models.AutoField(primary_key=True)

    journal_id = models.IntegerField(verbose_name="Jurnal ID")  # References Journal table

    # Personal Information (Names only)
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sharif")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    photo = models.ImageField(
        upload_to='editors_photos/',
        blank=True,
        null=True,
        help_text="Editor photograph"
    )

    # Professional Information (Essential details)
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Ilmiy daraja/unvon")
    affiliation = models.CharField(max_length=500, blank=True, null=True, verbose_name="Tashkilot")
    position = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lavozim")

    # Editor Type
    editor_type = models.CharField(max_length=20, choices=EDITOR_TYPES, default='associate',
                                   verbose_name="Muharrir turi")

    # Status and Order
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'journal_editors'
        ordering = ['editor_type', 'last_name', 'first_name']
        verbose_name = "Muharrir"
        verbose_name_plural = "Muharrirlar"
        indexes = [
            models.Index(fields=['journal_id']),
            models.Index(fields=['editor_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_editor_type_display()}"

    @property
    def full_name(self):
        """Return full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self):
        """Return short name with initials"""
        if self.middle_name:
            return f"{self.first_name[0]}. {self.middle_name[0]}. {self.last_name}"
        return f"{self.first_name[0]}. {self.last_name}"


class JournalPolicy(models.Model):
    """Policies for each journal"""
    POLICY_TYPES = [
        ('submission', 'Maqola yuborish qoidalari'),
        ('review', 'Ko\'rib chiqish jarayoni'),
        ('publication', 'Nashr etish siyosati'),
        ('ethics', 'Axloqiy qoidalar'),
        ('copyright', 'Mualliflik huquqi'),
        ('open_access', 'Ochiq kirish siyosati'),
        ('plagiarism', 'Plagiat siyosati'),
        ('retraction', 'Maqola qaytarish siyosati'),
        ('editorial', 'Tahririyat siyosati'),
        ('author_guidelines', 'Mualliflar uchun qo\'llanma'),
        ('reviewer_guidelines', 'Taqrizchilar uchun qo\'llanma'),
        ('privacy', 'Maxfiylik siyosati'),
        ('conflict_of_interest', 'Manfaatlar to\'qnashuvi'),
        ('data_sharing', 'Ma\'lumotlarni baham ko\'rish'),
        ('archiving', 'Arxivlash siyosati'),
    ]

    journal = models.ForeignKey('Journal', on_delete=models.CASCADE, related_name='policies')
    policy_type = models.CharField(max_length=30, choices=POLICY_TYPES, verbose_name="Siyosat turi")
    title = models.CharField(max_length=300, verbose_name="Sarlavha")
    content = models.TextField(verbose_name="Mazmun")

    # Additional content
    short_description = models.TextField(blank=True, null=True, verbose_name="Qisqacha tavsif")
    requirements = models.TextField(blank=True, null=True, verbose_name="Talablar")
    examples = models.TextField(blank=True, null=True, verbose_name="Misollar")

    # Settings
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_public = models.BooleanField(default=True, verbose_name="Ommaviy")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    # Metadata
    language = models.CharField(max_length=5, default='uz', choices=[
        ('uz', 'O\'zbek'),
        ('en', 'English'),
        ('ru', 'Русский'),
    ], verbose_name="Til")

    # SEO
    meta_description = models.CharField(max_length=160, blank=True, null=True, verbose_name="Meta tavsif")
    keywords = models.CharField(max_length=500, blank=True, null=True, verbose_name="Kalit so'zlar")

    # Version control
    version = models.CharField(max_length=10, default='1.0', verbose_name="Versiya")
    effective_date = models.DateField(default=timezone.now, verbose_name="Kuchga kirgan sana")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Oxirgi yangilanish")

    # Author information
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Yaratuvchi")
    updated_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Yangilovchi")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'policy_type', 'title']
        verbose_name = "Siyosat"
        verbose_name_plural = "Siyosatlar"
        unique_together = ['journal', 'policy_type']

    def __str__(self):
        return f"{self.title} ({self.journal.title})"

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.get_policy_type_display()
        super().save(*args, **kwargs)

    @property
    def content_preview(self):
        """Return first 200 characters of content"""
        if len(self.content) > 200:
            return self.content[:200] + '...'
        return self.content

    @property
    def word_count(self):
        """Return approximate word count"""
        return len(self.content.split())


class Issue(TimeStampedModel):
    """Journal issue model - optimized for Google Scholar indexing"""
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='issues')
    volume = models.IntegerField(validators=[MinValueValidator(1)])
    number = models.IntegerField(validators=[MinValueValidator(1)])
    year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        default=timezone.now().year
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this is the current active issue. Only one issue per journal may be active."
    )

    # Issue Details
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Special issue title (optional)"
    )
    description = models.TextField(
        blank=True,
        help_text="Issue description or editorial note"
    )

    # Publishing Information
    date_published = models.DateField(default=timezone.now)
    is_published = models.BooleanField(default=False)

    # SEO Fields
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description for this issue"
    )

    # Visual
    cover_image = models.ImageField(
        upload_to='issue_covers/%Y/',
        blank=True,
        null=True,
        help_text="Issue cover image"
    )

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        ordering = ['-year', '-volume', '-number']
        unique_together = ['journal', 'volume', 'number', 'year']

    def __str__(self):
        return f"{self.journal.title} Vol.{self.volume} No.{self.number} ({self.year})"

    @property
    def full_citation(self):
        """Full citation format for the issue"""
        return f"Vol.{self.volume}, No.{self.number} ({self.year})"

    # @property
    # def article_count(self) -> int:
    #     return self.articles.count()

    @property
    def issue_identifier(self):
        """Unique identifier for the issue"""
        return f"{self.year}-{self.volume}-{self.number}"

    def get_absolute_url(self):
        return reverse('issue_detail', kwargs={
            'journal_slug': self.journal.url_slug,
            'year': self.year,
            'volume': self.volume,
            'number': self.number
        })


class Author(TimeStampedModel):
    """Author model - optimized for scholarly indexing"""
    # Personal Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    # Professional Information
    affiliation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Institution/University affiliation"
    )
    department = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Academic position/title")

    # New fields (TEXT, not choices)
    academic_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ilmiy unvon (masalan: Professor, Dotsent, Katta ilmiy xodim)"
    )

    academic_degree = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ilmiy daraja (masalan: Fan doktori (DSc), Falsafa doktori (PhD), Fan nomzodi)"
    )

    # Contact Information
    email = models.EmailField(unique=True)
    website = models.URLField(blank=True)

    # Academic Identifiers - Important for Google Scholar
    orcid = models.CharField(
        max_length=50,
        blank=True,
        help_text="ORCID ID (e.g., 0000-0000-0000-0000)"
    )
    google_scholar_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Google Scholar profile ID"
    )
    researchgate_profile = models.URLField(blank=True)

    # Biography and Image
    bio = models.TextField(blank=True, help_text="Author biography")
    photo = models.ImageField(
        upload_to='author_photos/',
        blank=True,
        null=True,
        help_text="Author photograph"
    )

    # Settings
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts)

    @property
    def citation_name(self):
        """Name format for citations - Last, F. M."""
        if self.middle_name:
            return f"{self.last_name}, {self.first_name[0]}. {self.middle_name[0]}."
        return f"{self.last_name}, {self.first_name[0]}."

    @property
    def reverse_name(self):
        """Last, First Middle format"""
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"

    def get_absolute_url(self):
        return reverse('author_detail', kwargs={'author_id': self.pk})


class File(TimeStampedModel):
    """File model for article PDFs and supplementary materials"""
    # UUID for security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        ArticleSubmission,
        on_delete=models.CASCADE,
        related_name='files',
        help_text="Associated article submission",
        blank=True,
        null=True,
    )

    # File Information
    file = models.FileField(upload_to='article_files/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)

    # File Type Classification
    FILE_TYPES = [
        ('pdf', 'PDF Document'),
        ('supplement', 'Supplementary Material'),
        ('figure', 'Figure'),
        ('table', 'Table'),
        ('dataset', 'Dataset'),
        ('other', 'Other'),
    ]
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='pdf')

    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files'
    )
    description = models.TextField(blank=True, help_text="File description")

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"
        ordering = ['-created_at']

    def __str__(self):
        return self.original_filename

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class Article(TimeStampedModel):
    """Article model - heavily optimized for Google/Google Scholar indexing"""
    # Basic Information
    title = models.CharField(max_length=500, help_text="Article title")
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    abstract = models.TextField(help_text="Article abstract")
    references = models.TextField(null=True, blank=True, help_text="Article references")
    diploma_sent = models.BooleanField(default=False, help_text="Diploma has been sent to authors")
    keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Keywords separated by commas"
    )

    # Publication Details
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )

    # # Important Dates for Indexing
    # date_received = models.DateField(
    #     blank=True,
    #     null=True,
    #     help_text="Date manuscript was received"
    # )
    # date_accepted = models.DateField(
    #     blank=True,
    #     null=True,
    #     help_text="Date manuscript was accepted"
    # )
    date_published = models.DateField(
        default=timezone.now,
        help_text="Date article was published"
    )

    # Files
    main_pdf = models.ForeignKey(
        File,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='article_pdf',
        help_text="Main article PDF file"
    )
    supplementary_files = models.ManyToManyField(
        File,
        blank=True,
        related_name='supplementary_articles',
        help_text="Additional files (figures, datasets, etc.)"
    )

    # Authors Relationship
    authors = models.ManyToManyField(Author, through='ArticleAuthor')

    # Page Information - Important for Citations
    first_page = models.PositiveIntegerField(blank=True, null=True)
    last_page = models.PositiveIntegerField(blank=True, null=True)

    # Identifiers - Critical for Indexing
    doi = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Digital Object Identifier (DOI)"
    )

    # Note: FanTarmoq and IlmiyNashr are separate models, not connected to articles

    # SEO and Indexing Fields
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description"
    )
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    # Access and Display Settings
    open_access = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    # Metrics
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)

    # Language
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="Article language code (en, uz, ru)"
    )

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-date_published', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:200]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def page_range(self):
        """Return page range as string"""
        if self.first_page and self.last_page:
            return f"{self.first_page}-{self.last_page}"
        return ""

    @property
    def author_list(self):
        """Get ordered list of authors"""
        return self.authors.through.objects.filter(article=self).order_by('order')

    @property
    def citation(self):
        """Generate citation in standard format"""
        authors = []
        for article_author in self.author_list[:6]:  # Limit to first 6 authors
            authors.append(article_author.author.citation_name)

        if self.author_list.count() > 6:
            authors.append("et al.")

        author_string = ", ".join(authors)
        year = self.date_published.year

        if self.issue:
            journal_info = f"{self.issue.journal.title}, {self.issue.full_citation}"
        else:
            journal_info = "Unpublished"

        page_info = f", pp. {self.page_range}" if self.page_range else ""
        doi_info = f". DOI: {self.doi}" if self.doi else ""

        return f"{author_string} ({year}). {self.title}. {journal_info}{page_info}{doi_info}"

    @property
    def apa_citation(self):
        """Generate APA style citation"""
        # This is useful for Google Scholar
        authors = []
        for article_author in self.author_list:
            author = article_author.author
            if author.middle_name:
                authors.append(f"{author.last_name}, {author.first_name[0]}. {author.middle_name[0]}.")
            else:
                authors.append(f"{author.last_name}, {author.first_name[0]}.")

        if len(authors) > 1:
            author_string = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_string = authors[0] if authors else "Unknown Author"

        year = self.date_published.year

        if self.issue:
            journal_title = self.issue.journal.title
            volume_issue = f"{self.issue.volume}({self.issue.number})"
        else:
            journal_title = "Unknown Journal"
            volume_issue = ""

        page_info = f", {self.page_range}" if self.page_range else ""
        doi_info = f" https://doi.org/{self.doi}" if self.doi else ""

        return f"{author_string} ({year}). {self.title}. {journal_title}, {volume_issue}{page_info}.{doi_info}"

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Increment view counter"""
        self.views += 1
        self.save(update_fields=['views'])

    def increment_downloads(self):
        """Increment download counter"""
        self.downloads += 1
        self.save(update_fields=['downloads'])

    def get_keywords_list(self):
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',')]
        return []


class ArticleAuthor(models.Model):
    """Through model for article-author relationship with ordering"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Author order in publication (0 = first author)"
    )
    is_corresponding = models.BooleanField(
        default=False,
        help_text="Is this the corresponding author?"
    )
    contribution = models.TextField(
        blank=True,
        help_text="Author's specific contribution to the work"
    )

    class Meta:
        verbose_name = "Article Author"
        verbose_name_plural = "Article Authors"
        ordering = ['order']
        unique_together = ['article', 'author']

    def __str__(self):
        return f"{self.author} - {self.article.title[:30]}..."


class SiteSEO(models.Model):
    meta_title = models.CharField(max_length=200, blank=True, null=True, help_text="Site-wide meta title")
    meta_description = models.TextField(blank=True, null=True, help_text="Site-wide meta description")
    meta_keywords = models.TextField(blank=True, null=True, help_text="Site-wide keywords, comma-separated")
    publisher_name = models.CharField(max_length=200, blank=True, null=True, help_text="Publisher name for indexing")
    enable_google_scholar = models.BooleanField(default=False, help_text="Enable Google Scholar indexing")
    auto_sitemap = models.BooleanField(default=True, help_text="Auto-generate sitemap")

    class Meta:
        verbose_name = "Site SEO Settings"
        verbose_name_plural = "Site SEO Settings"

    def __str__(self):
        return "SEO Settings"
