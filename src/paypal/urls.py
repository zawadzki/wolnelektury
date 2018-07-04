# -*- coding: utf-8 -*-
# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django.conf.urls import url
from . import views

urlpatterns = (
    url(r'^form/$', views.paypal_form, name='paypal_form'),
    url(r'^return/$', views.paypal_return, name='paypal_return'),
    url(r'^cancel/$', views.paypal_cancel, name='paypal_cancel'),
)
