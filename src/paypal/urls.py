# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = (
    path('form/', RedirectView.as_view(url='/towarzystwo/dolacz/')),
    path('app-form/', RedirectView.as_view(url='/towarzystwo/dolacz/app/')),

    path('return/<key>/', views.paypal_return, name='paypal_return'),
    path('app-return/<key>/', views.paypal_return, kwargs={'app': True}, name='paypal_app_return'),
    path('cancel/', views.paypal_cancel, name='paypal_cancel'),
)
