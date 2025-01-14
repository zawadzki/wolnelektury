# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from datetime import date, datetime
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import models
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _, override
import getpaid
from catalogue.models import Book
from catalogue.utils import get_random_hash
from polls.models import Poll
from wolnelektury.utils import cached_render, clear_cached_renders
from . import app_settings


class Offer(models.Model):
    """ A fundraiser for a particular book. """
    author = models.CharField(_('author'), max_length=255)
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'))
    description = models.TextField(_('description'), blank=True)
    target = models.DecimalField(_('target'), decimal_places=2, max_digits=10)
    start = models.DateField(_('start'), db_index=True)
    end = models.DateField(_('end'), db_index=True)
    redakcja_url = models.URLField(_('redakcja URL'), blank=True)
    book = models.ForeignKey(Book, models.PROTECT, null=True, blank=True, help_text=_('Published book.'))
    cover = models.ImageField(_('Cover'), upload_to='funding/covers')
    poll = models.ForeignKey(Poll, help_text=_('Poll'), null=True, blank=True, on_delete=models.SET_NULL)

    notified_near = models.DateTimeField(_('Near-end notifications sent'), blank=True, null=True)
    notified_end = models.DateTimeField(_('End notifications sent'), blank=True, null=True)

    def cover_img_tag(self):
        return mark_safe('<img src="%s" />' % self.cover.url)
    cover_img_tag.short_description = _('Cover preview')

    class Meta:
        verbose_name = _('offer')
        verbose_name_plural = _('offers')
        ordering = ['-end']

    def __str__(self):
        return "%s - %s" % (self.author, self.title)

    def get_absolute_url(self):
        return reverse('funding_offer', args=[self.slug])

    def save(self, *args, **kw):
        published_now = (
            self.book_id is not None and self.pk is not None and
            type(self).objects.values('book').get(pk=self.pk)['book'] != self.book_id)
        retval = super(Offer, self).save(*args, **kw)
        self.clear_cache()
        if published_now:
            self.notify_published()
        return retval

    def clear_cache(self):
        clear_cached_renders(self.top_bar)
        clear_cached_renders(self.list_bar)
        clear_cached_renders(self.detail_bar)
        clear_cached_renders(self.status)
        clear_cached_renders(self.status_more)

    def is_current(self):
        return self.start <= date.today() <= self.end and self == self.current()

    def is_win(self):
        return self.sum() >= self.target

    def remaining(self):
        if self.is_current():
            return None
        if self.is_win():
            return self.sum() - self.target
        else:
            return self.sum()

    @classmethod
    def current(cls):
        """ Returns current fundraiser or None.

        Current fundraiser is the one that:
        - has already started,
        - hasn't yet ended,
        - if there's more than one of those, it's the one that ends last.

        """
        today = date.today()
        objects = cls.objects.filter(start__lte=today, end__gte=today).order_by('-end')
        try:
            return objects[0]
        except IndexError:
            return None

    @classmethod
    def past(cls):
        """ QuerySet for all past fundraisers. """
        objects = cls.public()
        current = cls.current()
        if current is not None:
            objects = objects.exclude(pk=current.pk)
        return objects

    @classmethod
    def public(cls):
        """ QuerySet for all current and past fundraisers. """
        today = date.today()
        return cls.objects.filter(start__lte=today)

    def get_perks(self, amount=None):
        """ Finds all the perks for the offer.

        If amount is provided, returns the perks you get for it.

        """
        perks = Perk.objects.filter(
                models.Q(offer=self) | models.Q(offer=None)
            ).exclude(end_date__lt=date.today())
        if amount is not None:
            perks = perks.filter(price__lte=amount)
        return perks

    def funding_payed(self):
        """ QuerySet for all completed payments for the offer. """
        return Funding.payed().filter(offer=self)

    def funders(self):
        return self.funding_payed().order_by('-amount', 'payed_at')

    def sum(self):
        """ The money gathered. """
        return self.funding_payed().aggregate(s=models.Sum('amount'))['s'] or 0

    def notify_all(self, subject, template_name, extra_context=None):
        Funding.notify_funders(
            subject, template_name, extra_context,
            query_filter=models.Q(offer=self)
        )

    def notify_end(self, force=False):
        if not force and self.notified_end:
            return
        assert not self.is_current()
        self.notify_all(
            _('The fundraiser has ended!'),
            'funding/email/end.txt', {
                'offer': self,
                'is_win': self.is_win(),
                'remaining': self.remaining(),
                'current': self.current(),
            })
        self.notified_end = datetime.utcnow().replace(tzinfo=utc)
        self.save()

    def notify_near(self, force=False):
        if not force and self.notified_near:
            return
        assert self.is_current()
        sum_ = self.sum()
        need = self.target - sum_
        self.notify_all(
            _('The fundraiser will end soon!'),
            'funding/email/near.txt', {
                'days': (self.end - date.today()).days + 1,
                'offer': self,
                'is_win': self.is_win(),
                'sum': sum_,
                'need': need,
            })
        self.notified_near = datetime.utcnow().replace(tzinfo=utc)
        self.save()

    def notify_published(self):
        assert self.book is not None
        self.notify_all(
            _('The book you helped fund has been published.'),
            'funding/email/published.txt', {
                'offer': self,
                'book': self.book,
                'author': self.book.pretty_title(),
                'current': self.current(),
            })

    def basic_info(self):
        offer_sum = self.sum()
        return {
            'offer': self,
            'sum': offer_sum,
            'is_current': self.is_current(),
            'is_win': offer_sum >= self.target,
            'missing': self.target - offer_sum,
            'percentage': 100 * offer_sum / self.target,

            'show_title': True,
            'show_title_calling': True,
        }

    @cached_render('funding/includes/funding.html')
    def top_bar(self):
        ctx = self.basic_info()
        ctx.update({
            'link': True,
            'closeable': True,
            'add_class': 'funding-top-header',
        })
        return ctx

    @cached_render('funding/includes/funding.html')
    def list_bar(self):
        ctx = self.basic_info()
        ctx.update({
            'link': True,
            'show_title_calling': False,
        })
        return ctx

    @cached_render('funding/includes/funding.html')
    def detail_bar(self):
        ctx = self.basic_info()
        ctx.update({
            'show_title': False,
        })
        return ctx

    @cached_render('funding/includes/offer_status.html')
    def status(self):
        return {'offer': self}

    @cached_render('funding/includes/offer_status_more.html')
    def status_more(self):
        return {'offer': self}


class Perk(models.Model):
    """ A perk offer.

    If no attached to a particular Offer, applies to all.

    """
    offer = models.ForeignKey(Offer, models.CASCADE, verbose_name=_('offer'), null=True, blank=True)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=10)
    name = models.CharField(_('name'), max_length=255)
    long_name = models.CharField(_('long name'), max_length=255)
    end_date = models.DateField(_('end date'), null=True, blank=True)

    class Meta:
        verbose_name = _('perk')
        verbose_name_plural = _('perks')
        ordering = ['-price']

    def __str__(self):
        return "%s (%s%s)" % (self.name, self.price, " for %s" % self.offer if self.offer else "")


class Funding(models.Model):
    """ A person paying in a fundraiser.

    The payment was completed if and only if payed_at is set.

    """
    offer = models.ForeignKey(Offer, models.PROTECT, verbose_name=_('offer'))
    name = models.CharField(_('name'), max_length=127, blank=True)
    email = models.EmailField(_('email'), blank=True, db_index=True)
    amount = models.DecimalField(_('amount'), decimal_places=2, max_digits=10)
    payed_at = models.DateTimeField(_('payed at'), null=True, blank=True, db_index=True)
    perks = models.ManyToManyField(Perk, verbose_name=_('perks'), blank=True)
    language_code = models.CharField(max_length=2, null=True, blank=True)
    notifications = models.BooleanField(_('notifications'), default=True, db_index=True)
    notify_key = models.CharField(max_length=32)

    class Meta:
        verbose_name = _('funding')
        verbose_name_plural = _('fundings')
        ordering = ['-payed_at', 'pk']

    @classmethod
    def payed(cls):
        """ QuerySet for all completed payments. """
        return cls.objects.exclude(payed_at=None)

    def __str__(self):
        return str(self.offer)

    def get_absolute_url(self):
        return reverse('funding_funding', args=[self.pk])

    def perk_names(self):
        return ", ".join(perk.name for perk in self.perks.all())

    def get_disable_notifications_url(self):
        return "%s?%s" % (
            reverse("funding_disable_notifications"),
            urlencode({
                'email': self.email,
                'key': self.notify_key,
            }))

    def wl_optout_url(self):
        return 'https://wolnelektury.pl' + self.get_disable_notifications_url()

    def save(self, *args, **kwargs):
        if self.email and not self.notify_key:
            self.notify_key = get_random_hash(self.email)
        ret = super(Funding, self).save(*args, **kwargs)
        self.offer.clear_cache()
        return ret

    @classmethod
    def notify_funders(cls, subject, template_name, extra_context=None, query_filter=None, payed_only=True):
        funders = cls.objects.exclude(email="").filter(notifications=True)
        if payed_only:
            funders = funders.exclude(payed_at=None)
        if query_filter is not None:
            funders = funders.filter(query_filter)
        emails = set()
        for funder in funders:
            if funder.email in emails:
                continue
            emails.add(funder.email)
            funder.notify(subject, template_name, extra_context)

    def notify(self, subject, template_name, extra_context=None):
        context = {
            'funding': self,
            'site': Site.objects.get_current(),
        }
        if extra_context:
            context.update(extra_context)
        with override(self.language_code or app_settings.DEFAULT_LANGUAGE):
            send_mail(
                subject, render_to_string(template_name, context), settings.CONTACT_EMAIL, [self.email],
                fail_silently=False)

    def disable_notifications(self):
        """Disables all notifications for this e-mail address."""
        type(self).objects.filter(email=self.email).update(notifications=False)


# Register the Funding model with django-getpaid for payments.
getpaid.register_to_payment(Funding, unique=False, related_name='payment')


class Spent(models.Model):
    """ Some of the remaining money spent on a book. """
    book = models.ForeignKey(Book, models.PROTECT)
    amount = models.DecimalField(_('amount'), decimal_places=2, max_digits=10)
    timestamp = models.DateField(_('when'))

    class Meta:
        verbose_name = _('money spent on a book')
        verbose_name_plural = _('money spent on books')
        ordering = ['-timestamp']

    def __str__(self):
        return "Spent: %s" % str(self.book)


@receiver(getpaid.signals.new_payment_query)
def new_payment_query_listener(sender, order=None, payment=None, **kwargs):
    """ Set payment details for getpaid. """
    payment.amount = order.amount
    payment.currency = 'PLN'


@receiver(getpaid.signals.user_data_query)
def user_data_query_listener(sender, order, user_data, **kwargs):
    """ Set user data for payment. """
    user_data['email'] = order.email


@receiver(getpaid.signals.payment_status_changed)
def payment_status_changed_listener(sender, instance, old_status, new_status, **kwargs):
    """ React to status changes from getpaid. """
    if old_status != 'paid' and new_status == 'paid':
        instance.order.payed_at = datetime.utcnow().replace(tzinfo=utc)
        instance.order.save()
        if instance.order.email:
            instance.order.notify(
                _('Thank you for your support!'),
                'funding/email/thanks.txt'
            )
