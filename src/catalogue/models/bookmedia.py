# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from collections import OrderedDict
import json
from collections import namedtuple
from django.db import models
from django.utils.translation import ugettext_lazy as _
from slugify import slugify
from mutagen import MutagenError

from catalogue.fields import OverwriteStorage


def _file_upload_to(i, _n):
    name = i.book.slug
    if i.index:
        name += f'_{i.index:03d}'
    if i.part_name:
        name += f'_' + slugify(i.part_name)
    ext = i.ext()
    return f'book/{ext}/{name}.{ext}'


class BookMedia(models.Model):
    """Represents media attached to a book."""
    FileFormat = namedtuple("FileFormat", "name ext")
    formats = OrderedDict([
        ('mp3', FileFormat(name='MP3', ext='mp3')),
        ('ogg', FileFormat(name='Ogg Vorbis', ext='ogg')),
        ('daisy', FileFormat(name='DAISY', ext='daisy.zip')),
    ])
    format_choices = [(k, _('%s file' % t.name)) for k, t in formats.items()]

    type = models.CharField(_('type'), db_index=True, choices=format_choices, max_length=20)
    name = models.CharField(_('name'), max_length=512)
    part_name = models.CharField(_('part name'), default='', blank=True, max_length=512)
    index = models.IntegerField(_('index'), default=0)
    file = models.FileField(_('file'), max_length=600, upload_to=_file_upload_to, storage=OverwriteStorage())
    uploaded_at = models.DateTimeField(_('creation date'), auto_now_add=True, editable=False, db_index=True)
    project_description = models.CharField(max_length=2048, blank=True)
    project_icon = models.CharField(max_length=2048, blank=True)
    extra_info = models.TextField(_('extra information'), default='{}', editable=False)
    book = models.ForeignKey('Book', models.CASCADE, related_name='media')
    source_sha1 = models.CharField(null=True, blank=True, max_length=40, editable=False)

    def __str__(self):
        return self.file.name.split("/")[-1]

    class Meta:
        ordering = ('type', 'index')
        verbose_name = _('book media')
        verbose_name_plural = _('book media')
        app_label = 'catalogue'

    def get_extra_info_json(self):
        return json.loads(self.extra_info or '{}')

    def get_nice_filename(self):
        parts_count = 1 + type(self).objects.filter(book=self.book, type=self.type).exclude(pk=self.pk).count()

        name = self.book.slug
        if parts_count > 0:
            name += f'_{self.index:03d}'
        if self.part_name:
            name += f'_' + slugify(self.part_name)
        ext = self.ext()
        return f'{name}.{ext}'

    def save(self, parts_count=None, *args, **kwargs):
        from catalogue.utils import ExistingFile, remove_zip

        if not parts_count:
            parts_count = 1 + BookMedia.objects.filter(book=self.book, type=self.type).exclude(pk=self.pk).count()
        if parts_count == 1:
            self.name = self.book.pretty_title()
        else:
            no = ('%02d' if parts_count < 100 else '%03d') % self.index
            self.name = '%s. %s' % (no, self.book.pretty_title())
            if self.part_name:
                self.name += ', ' + self.part_name

        try:
            old = BookMedia.objects.get(pk=self.pk)
        except BookMedia.DoesNotExist:
            old = None

        super(BookMedia, self).save(*args, **kwargs)
        
        # remove the zip package for book with modified media
        if old:
            remove_zip("%s_%s" % (old.book.slug, old.type))
        remove_zip("%s_%s" % (self.book.slug, self.type))

        extra_info = self.get_extra_info_json()
        extra_info.update(self.read_meta())
        self.extra_info = json.dumps(extra_info)
        self.source_sha1 = self.read_source_sha1(self.file.path, self.type)
        return super(BookMedia, self).save(*args, **kwargs)

    def read_meta(self):
        """
            Reads some metadata from the audiobook.
        """
        import mutagen
        from mutagen import id3

        artist_name = director_name = project = funded_by = license = ''
        if self.type == 'mp3':
            try:
                audio = id3.ID3(self.file.path)
                artist_name = ', '.join(', '.join(tag.text) for tag in audio.getall('TPE1'))
                director_name = ', '.join(', '.join(tag.text) for tag in audio.getall('TPE3'))
                license = ', '.join(tag.url for tag in audio.getall('WCOP'))
                project = ", ".join([
                    t.data.decode('utf-8') for t in audio.getall('PRIV')
                    if t.owner == 'wolnelektury.pl?project'])
                funded_by = ", ".join([
                    t.data.decode('utf-8') for t in audio.getall('PRIV')
                    if t.owner == 'wolnelektury.pl?funded_by'])
            except MutagenError:
                pass
        elif self.type == 'ogg':
            try:
                audio = mutagen.File(self.file.path)
                artist_name = ', '.join(audio.get('artist', []))
                director_name = ', '.join(audio.get('conductor', []))
                license = ', '.join(audio.get('license', []))
                project = ", ".join(audio.get('project', []))
                funded_by = ", ".join(audio.get('funded_by', []))
            except (MutagenError, AttributeError):
                pass
        else:
            return {}
        return {'artist_name': artist_name, 'director_name': director_name,
                'project': project, 'funded_by': funded_by, 'license': license}

    def ext(self):
        return self.formats[self.type].ext

    @staticmethod
    def read_source_sha1(filepath, filetype):
        """
            Reads source file SHA1 from audiobok metadata.
        """
        import mutagen
        from mutagen import id3

        if filetype == 'mp3':
            try:
                audio = id3.ID3(filepath)
                return [t.data.decode('utf-8') for t in audio.getall('PRIV')
                        if t.owner == 'wolnelektury.pl?flac_sha1'][0]
            except (MutagenError, IndexError):
                return None
        elif filetype == 'ogg':
            try:
                audio = mutagen.File(filepath)
                return audio.get('flac_sha1', [None])[0]
            except (MutagenError, AttributeError, IndexError):
                return None
        else:
            return None

    @property
    def director(self):
        return self.get_extra_info_json().get('director_name', None)

    @property
    def artist(self):
        return self.get_extra_info_json().get('artist_name', None)

    def file_url(self):
        return self.file.url
