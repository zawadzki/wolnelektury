# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import Prefetch
from django.dispatch import Signal
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from newtagging.models import TagManager, TaggedItemManager


# Those are hard-coded here so that makemessages sees them.
TAG_CATEGORIES = (
    ('author', _('author')),
    ('epoch', _('epoch')),
    ('kind', _('kind')),
    ('genre', _('genre')),
    ('theme', _('theme')),
    ('set', _('set')),
    ('thing', _('thing')),  # things shown on pictures
)


class TagRelation(models.Model):

    tag = models.ForeignKey('Tag', models.CASCADE, verbose_name=_('tag'), related_name='items')
    content_type = models.ForeignKey(ContentType, models.CASCADE, verbose_name=_('content type'))
    object_id = models.PositiveIntegerField(_('object id'), db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = TaggedItemManager()

    class Meta:
        db_table = 'catalogue_tag_relation'
        unique_together = (('tag', 'content_type', 'object_id'),)

    def __str__(self):
        try:
            return '%s [%s]' % (self.content_type.get_object_for_this_type(pk=self.object_id), self.tag)
        except ObjectDoesNotExist:
            return '<deleted> [%s]' % self.tag


class Tag(models.Model):
    """A tag attachable to books and fragments (and possibly anything).

    Used to represent searchable metadata (authors, epochs, genres, kinds),
    fragment themes (motifs) and some book hierarchy related kludges."""
    name = models.CharField(_('name'), max_length=120, db_index=True)
    slug = models.SlugField(_('slug'), max_length=120, db_index=True)
    sort_key = models.CharField(_('sort key'), max_length=120, db_index=True)
    category = models.CharField(
        _('category'), max_length=50, blank=False, null=False, db_index=True, choices=TAG_CATEGORIES)
    description = models.TextField(_('description'), blank=True)

    for_books = models.BooleanField(default=False)
    for_pictures = models.BooleanField(default=False)

    user = models.ForeignKey(User, models.CASCADE, blank=True, null=True)
    gazeta_link = models.CharField(blank=True, max_length=240)
    culturepl_link = models.CharField(blank=True, max_length=240)
    wiki_link = models.CharField(blank=True, max_length=240)
    photo = models.FileField(blank=True, null=True, upload_to='catalogue/tag/')
    photo_attribution = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(_('creation date'), auto_now_add=True, db_index=True)
    changed_at = models.DateTimeField(_('creation date'), auto_now=True, db_index=True)

    after_change = Signal(providing_args=['instance'])

    intermediary_table_model = TagRelation
    objects = TagManager()

    class UrlDeprecationWarning(DeprecationWarning):
        def __init__(self, tags=None):
            super(Tag.UrlDeprecationWarning, self).__init__()
            self.tags = tags

    categories_rev = {
        'autor': 'author',
        'epoka': 'epoch',
        'rodzaj': 'kind',
        'gatunek': 'genre',
        'motyw': 'theme',
        'polka': 'set',
        'obiekt': 'thing',
    }
    categories_dict = dict((item[::-1] for item in categories_rev.items()))

    class Meta:
        ordering = ('sort_key',)
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        unique_together = (("slug", "category"),)
        app_label = 'catalogue'

    def save(self, *args, **kwargs):
        existing = self.pk and self.category != 'set'
        ret = super(Tag, self).save(*args, **kwargs)
        if existing:
            self.after_change.send(sender=type(self), instance=self)
        return ret

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Tag(slug=%r)" % self.slug

    def get_initial(self):
        if self.category == 'author':
            return self.sort_key[0]
        elif self.name:
            return self.name[0]
        else:
            return ''

    @property
    def category_plural(self):
        return self.category + 's'

    def get_absolute_url(self):
        return reverse('tagged_object_list', args=[self.url_chunk])

    def get_absolute_gallery_url(self):
        return reverse('tagged_object_list_gallery', args=[self.url_chunk])

    def has_description(self):
        return len(self.description) > 0
    has_description.short_description = _('description')
    has_description.boolean = True

    @staticmethod
    def get_tag_list(tag_str):
        if not tag_str:
            return []
        tags = []
        ambiguous_slugs = []
        category = None
        deprecated = False
        tags_splitted = tag_str.split('/')
        for name in tags_splitted:
            if category:
                tags.append(Tag.objects.get(slug=name, category=category))
                category = None
            elif name in Tag.categories_rev:
                category = Tag.categories_rev[name]
            else:
                try:
                    tags.append(Tag.objects.get(slug=name))
                    deprecated = True
                except Tag.MultipleObjectsReturned:
                    ambiguous_slugs.append(name)

        if category:
            # something strange left off
            raise Tag.DoesNotExist()
        if ambiguous_slugs:
            # some tags should be qualified
            e = Tag.MultipleObjectsReturned()
            e.tags = tags
            e.ambiguous_slugs = ambiguous_slugs
            raise e
        if deprecated:
            raise Tag.UrlDeprecationWarning(tags=tags)
        return tags

    @property
    def url_chunk(self):
        return '/'.join((Tag.categories_dict[self.category], self.slug))

    @staticmethod
    def tags_from_info(info):
        from slugify import slugify
        from sortify import sortify
        meta_tags = []
        categories = (('kinds', 'kind'), ('genres', 'genre'), ('authors', 'author'), ('epochs', 'epoch'))
        for field_name, category in categories:
            try:
                tag_names = getattr(info, field_name)
            except (AttributeError, KeyError):  # TODO: shouldn't be KeyError here at all.
                try:
                    tag_names = [getattr(info, category)]
                except KeyError:
                    # For instance, Pictures do not have 'genre' field.
                    continue
            for tag_name in tag_names:
                lang = getattr(tag_name, 'lang', settings.LANGUAGE_CODE)
                tag_sort_key = tag_name
                if category == 'author':
                    tag_sort_key = ' '.join((tag_name.last_name,) + tag_name.first_names)
                    tag_name = tag_name.readable()
                if lang == settings.LANGUAGE_CODE:
                    # Allow creating new tag, if it's in default language.
                    tag, created = Tag.objects.get_or_create(slug=slugify(tag_name), category=category)
                    if created:
                        tag_name = str(tag_name)
                        tag.name = tag_name
                        setattr(tag, "name_%s" % lang, tag_name)
                        tag.sort_key = sortify(tag_sort_key.lower())
                        tag.save()

                    meta_tags.append(tag)
                else:
                    # Ignore unknown tags in non-default languages.
                    try:
                        tag = Tag.objects.get(category=category, **{"name_%s" % lang: tag_name})
                    except Tag.DoesNotExist:
                        pass
                    else:
                        meta_tags.append(tag)
        return meta_tags


TagRelation.tag_model = Tag


def prefetch_relations(objects, category, only_name=True):
    queryset = TagRelation.objects.filter(tag__category=category).select_related('tag')
    if only_name:
        queryset = queryset.only('tag__name_pl', 'object_id')
    return objects.prefetch_related(
        Prefetch('tag_relations', queryset=queryset, to_attr='%s_relations' % category))


def prefetched_relations(obj, category):
    if hasattr(obj, '%s_relations' % category):
        return getattr(obj, '%s_relations' % category)
    else:
        return None
