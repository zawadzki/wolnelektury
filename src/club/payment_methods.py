from django.conf import settings
from django.urls import reverse


class PaymentMethod(object):
    is_recurring = False

    def initiate(self, request, schedule):
        return reverse('club_dummy_payment', args=[schedule.key])


class PayU(PaymentMethod):
    slug = 'payu'
    name = 'PayU'
    template_name = 'club/payment/payu.html'

    def __init__(self, pos_id):
        self.pos_id = pos_id

    def initiate(self, request, schedule):
        # Create Order at once.
        from .models import PayUOrder
        order = PayUOrder.objects.create(
            pos_id=self.pos_id,
            customer_ip=request.META['REMOTE_ADDR'],
            schedule=schedule,
        )
        return order.put()


class PayURe(PaymentMethod):
    slug='payu-re'
    name = 'PayU Recurring'
    template_name = 'club/payment/payu-re.html'
    is_recurring = True

    def __init__(self, pos_id):
        self.pos_id = pos_id

    def initiate(self, request, schedule):
        return reverse('club_payu_rec_payment', args=[schedule.key])

    def pay(self, request, schedule):
        # Create order, put it and see what happens next.
        from .models import PayUOrder
        order = PayUOrder.objects.create(
            pos_id=self.pos_id,
            customer_ip=request.META['REMOTE_ADDR'],
            schedule=schedule,
        )
        return order.put()
        

class PayPalRe(PaymentMethod):
    slug='paypal-re'
    name = 'PayPal Recurring'
    template_name = 'club/payment/paypal-re.html'
    is_recurring = True

    def initiate(self, request, schedule):
        return reverse('club_dummy_payment', args=[schedule.key])


methods = []

pos = getattr(settings, 'CLUB_PAYU_POS', None)
if pos:
    payu_method = PayU(pos)
    methods.append(payu_method)
else:
    payu_method = None

pos= getattr(settings, 'CLUB_PAYU_RECURRING_POS', None)
if pos:
    payure_method = PayURe(pos)
    methods.append(payure_method)
else:
    payure_method = None


methods.append(PayPalRe())


method_by_slug = {
    m.slug: m
    for m in methods
}
