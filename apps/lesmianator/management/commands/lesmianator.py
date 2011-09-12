# -*- coding: utf-8 -*-
# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
import re
import sys
from cPickle import load, dump
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.color import color_style
from django.conf import settings

from catalogue.models import Book, Tag

# extract text from text file
re_text = re_text = re.compile(r'\n{3,}(.*?)\n*-----\n', re.S).search


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-t', '--tags', dest='tags', metavar='SLUG,...',
            help='Use only books tagged with this tags'),
        make_option('-i', '--include', dest='include', metavar='SLUG,...',
            help='Include specific books by slug'),
        make_option('-e', '--exclude', dest='exclude', metavar='SLUG,...',
            help='Exclude specific books by slug')
    )
    help = 'Prepare data for Lesmianator.'

    def handle(self, *args, **options):
        self.style = color_style()
        verbose = int(options.get('verbosity'))
        tags = options.get('tags')
        include = options.get('include')
        exclude = options.get('exclude')

        try:
            path = settings.LESMIANATOR_PICKLE
        except:
            print self.style.ERROR('LESMIANATOR_PICKLE not set in the settings.')
            return

        books = []

        if include:
            books += list(Book.objects.filter(slug__in=include.split(',')).only('slug', 'txt_file'))

        if tags:
            books += list(Book.tagged.with_all(Tag.objects.filter(slug__in=tags.split(','))).only('slug', 'txt_file'))
        elif not include:
            books = list(Book.objects.all().only('slug', 'txt_file'))

        if exclude:
            books = [book for book in books if book.slug not in exclude.split(',')]

        books = set(books)

        lesmianator = {}
        processed = skipped = 0
        for book in books:
            if verbose >= 2:
                print 'Parsing', book.slug
            if not book.txt_file:
                if verbose >= 1:
                    print self.style.NOTICE('%s has no TXT file' % book.slug)
                skipped += 1
                continue
            with open(book.txt_file.path) as f:
                m = re_text(f.read())
                if not m:
                    print self.style.ERROR("Unknown text format: %s" % book.slug)
                    skipped += 1
                    continue

                processed += 1
                last_word = ''
                text = unicode(m.group(1), 'utf-8').lower()
                for letter in text:
                    mydict = lesmianator.setdefault(last_word, {})
                    myval = mydict.setdefault(letter, 0)
                    mydict[letter] += 1
                    last_word = last_word[-2:] + letter

        if not processed:
            if skipped:
                print self.style.ERROR("No books with TXT files found")
            else:
                print self.style.ERROR("No books found")
            return

        try:
            dump(lesmianator, open(path, 'w'))
        except:
            print self.style.ERROR("Couldn't write to $s" % path)
            return

        dump(lesmianator, open(path, 'w'))
        if verbose >= 1:
            print "%d processed, %d skipped" % (processed, skipped)
            print "Results dumped to %s" % path 
