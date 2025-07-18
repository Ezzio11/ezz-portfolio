from django.db import models
from django.utils.text import slugify

# Create your models here.

class Article(models.Model):
    SOURCE_CHOICES = [
        ('grimoire', 'The Grimoire'),
        ('mstag', 'MSTAG'),
    ]

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    linkedin_url = models.URLField(blank=True, null=True)
    external_url = models.URLField(blank=True, null=True, help_text="Link to ResearchGate, Google Scholar, etc.")
    slug = models.SlugField(unique=True)
    content = models.TextField(blank=True, null=True)  # Markdown or HTML
    description = models.TextField(blank=True, null=True)
    is_markdown = models.BooleanField(default=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='mstag')
    image = models.ImageField(upload_to='article_images/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='articles_pdfs/', blank=True, null=True)
    date_published = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.source.upper()}] {self.title}"
