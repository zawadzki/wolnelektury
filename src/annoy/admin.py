from django.contrib import admin
from django import forms
from modeltranslation.admin import TranslationAdmin
from . import models


class BannerAdmin(TranslationAdmin):
    list_display = [
            'place', 'text',
            'text_color', 'background_color',
            'priority', 'since', 'until',
            'show_members', 'staff_preview']


admin.site.register(models.Banner, BannerAdmin)


class DTITForm(forms.ModelForm):
    class Meta:
        model = models.DynamicTextInsertText
        fields = '__all__'
        widgets = {
            'background_color': forms.TextInput(attrs={"type": "color"}),
            'text_color': forms.TextInput(attrs={"type": "color"}),
        }


class DynamicTextInsertTextInline(admin.TabularInline):
    model = models.DynamicTextInsertText
    form = DTITForm
    fields = ['text', 'image', 'own_colors', 'background_color', 'text_color']
    extra = 0
    min_num = 1



class DynamicTextInsertAdmin(admin.ModelAdmin):
    list_display = ['paragraphs']
    inlines = [DynamicTextInsertTextInline]


admin.site.register(models.DynamicTextInsert, DynamicTextInsertAdmin)
