# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django import forms
from django.utils.translation import ugettext_lazy as _

from catalogue.models import Book
from waiter.models import WaitedFile
from django.core.exceptions import ValidationError
from catalogue.utils import get_customized_pdf_path
from catalogue.tasks import build_custom_pdf


class BookImportForm(forms.Form):
    book_xml_file = forms.FileField(required=False)
    book_xml = forms.CharField(required=False)
    gallery_url = forms.CharField(required=False)
    days = forms.IntegerField(required=False)
    hidden = forms.BooleanField(required=False)

    def clean(self):
        from django.core.files.base import ContentFile

        if not self.cleaned_data['book_xml_file']:
            if self.cleaned_data['book_xml']:
                self.cleaned_data['book_xml_file'] = \
                    ContentFile(self.cleaned_data['book_xml'].encode('utf-8'))
            else:
                raise forms.ValidationError(_("Please supply an XML."))
        return super(BookImportForm, self).clean()

    def save(self, **kwargs):
        return Book.from_xml_file(self.cleaned_data['book_xml_file'], overwrite=True,
                                  remote_gallery_url=self.cleaned_data['gallery_url'],
                                  days=self.cleaned_data['days'],
                                  findable=not self.cleaned_data['hidden'],
                                  **kwargs)


FORMATS = [(f, f.upper()) for f in Book.ebook_formats]


class DownloadFormatsForm(forms.Form):
    formats = forms.MultipleChoiceField(required=False, choices=FORMATS, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(DownloadFormatsForm, self).__init__(*args, **kwargs)


CUSTOMIZATION_FLAGS = (
    ('nofootnotes', _("Don't show footnotes")),
    ('nothemes', _("Don't disply themes")),
    ('nowlfont', _("Don't use our custom font")),
    ('nocover', _("Without cover")),
    ('notoc', _("Without table of contents")),
    )
CUSTOMIZATION_OPTIONS = (
    ('leading', _("Leading"), (
        ('', _('Normal leading')),
        ('onehalfleading', _('One and a half leading')),
        ('doubleleading', _('Double leading')),
    )),
    ('fontsize', _("Font size"), (
        ('', _('Default')),
        ('13pt', _('Big')),
        ('16pt', _('Bigger')),
    )),
    # ('pagesize', _("Paper size"), (
    #     ('a4paper', _('A4')),
    #     ('a5paper', _('A5')),
    # )),
)


class CustomPDFForm(forms.Form):
    def __init__(self, book, *args, **kwargs):
        super(CustomPDFForm, self).__init__(*args, **kwargs)
        self.book = book
        for name, label in CUSTOMIZATION_FLAGS:
            self.fields[name] = forms.BooleanField(required=False, label=label)
        for name, label, choices in CUSTOMIZATION_OPTIONS:
            self.fields[name] = forms.ChoiceField(choices=choices, required=False, label=label)

    def clean(self):
        self.cleaned_data['cust'] = self.customizations
        self.cleaned_data['path'] = get_customized_pdf_path(self.book, self.cleaned_data['cust'])
        if not WaitedFile.can_order(self.cleaned_data['path']):
            raise ValidationError(_('Queue is full. Please try again later.'))
        return self.cleaned_data

    @property
    def customizations(self):
        c = []
        for name, label in CUSTOMIZATION_FLAGS:
            if self.cleaned_data.get(name):
                c.append(name)
        for name, label, choices in CUSTOMIZATION_OPTIONS:
            option = self.cleaned_data.get(name)
            if option:
                c.append(option)
        c.sort()
        return c

    def save(self, *args, **kwargs):
        if not self.cleaned_data['cust'] and self.book.pdf_file:
            # Don't build with default options, just redirect to the standard file.
            return {"redirect": self.book.pdf_url()}
        url = WaitedFile.order(
            self.cleaned_data['path'],
            lambda p, waiter_id: build_custom_pdf.delay(self.book.id, self.cleaned_data['cust'], p, waiter_id),
            self.book.pretty_title()
        )
        return {"redirect": url}
