# -*- coding: utf-8 -*-
# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from fnpdjango.utils.text.textilepl import textile_pl

HONEYPOT_FIELD_NAME = 'miut'
PAGINATION_INVALID_PAGE_RAISES_404 = True
THUMBNAIL_QUALITY = 95

MODELTRANSLATION_DEFAULT_LANGUAGE = 'pl'
MODELTRANSLATION_PREPOPULATE_LANGUAGE = 'pl'

MIGRATION_MODULES = {
    'getpaid': 'wolnelektury.migrations.getpaid',
    'piston': 'wolnelektury.migrations.piston',
}

GETPAID_ORDER_DESCRIPTION = "{% load funding_tags %}{{ order|sanitize_payment_title }}"

PIWIK_URL = ''
PIWIK_SITE_ID = 0
PIWIK_TOKEN = ''

PAYPAL_CONFIG = {
    'mode': 'sandbox',  # sandbox or live
    'client_id': '',
    'client_secret': '',
}

MARKUP_FIELD_TYPES = (
    ('textile_pl', textile_pl),
)
