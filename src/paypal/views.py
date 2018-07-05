# -*- coding: utf-8 -*-
# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import render

from paypal.forms import PaypalSubscriptionForm
from paypal.rest import execute_agreement, check_agreement, agreement_approval_url, PaypalError
from paypal.models import BillingAgreement as BillingAgreementModel, BillingPlan


@login_required
def paypal_form(request):
    if request.POST:
        form = PaypalSubscriptionForm(data=request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                approval_url = agreement_approval_url(amount)
            except PaypalError as e:
                return render(request, 'paypal/error_page.html', {'error': e.message})
            return HttpResponseRedirect(approval_url)
    else:
        form = PaypalSubscriptionForm()
    return render(request, 'paypal/form.html', {'form': form})


@login_required
def paypal_return(request):
    token = request.GET.get('token')
    if not token:
        raise Http404
    if not BillingAgreementModel.objects.filter(token=token):
        resource = execute_agreement(token)
        if resource.id:
            amount = int(Decimal(resource.plan.payment_definitions[0].amount['value']))
            plan = BillingPlan.objects.get(amount=amount)
            active = check_agreement(resource.id)
            BillingAgreementModel.objects.create(
                agreement_id=resource.id, user=request.user, plan=plan, active=active, token=token)
    return render(request, 'paypal/return.html', {'resource': resource})


def paypal_cancel(request):
    return render(request, 'paypal/cancel.html', {})