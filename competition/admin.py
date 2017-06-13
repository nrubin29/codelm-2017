from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from solo.admin import SingletonModelAdmin

from competition.models import TestCase, TestCaseSubmission, GradedProblem, Team, Division, GradedSubmission, \
    UploadProblem, FileSubmission, UploadSubmission, Settings


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0


class TestCaseSubmissionInline(admin.TabularInline):
    model = TestCaseSubmission
    extra = 0


class FileSubmissionInline(admin.TabularInline):
    model = FileSubmission
    extra = 0


class TeamAdmin(admin.ModelAdmin):
    list_display = ('user', 'division')
    ordering = ('division',)


class GradedProblemAdminForm(forms.ModelForm):
    class Meta:
        model = GradedProblem
        exclude = []
        widgets = {
            'divisions': FilteredSelectMultiple(is_stacked=False, verbose_name='divisions'),
        }


class GradedProblemAdmin(admin.ModelAdmin):
    inlines = [
        TestCaseInline,
    ]

    form = GradedProblemAdminForm

    list_display = ('name', 'divisions_display')
    ordering = ('order',)

    def divisions_display(self, obj):
        return ', '.join(map(str, obj.divisions.all()))


class GradedSubmissionAdmin(admin.ModelAdmin):
    inlines = [
        TestCaseSubmissionInline,
    ]


class UploadProblemAdminForm(forms.ModelForm):
    class Meta:
        model = UploadProblem
        exclude = []
        widgets = {
            'divisions': FilteredSelectMultiple(is_stacked=False, verbose_name='divisions'),
        }


class UploadProblemAdmin(admin.ModelAdmin):
    form = UploadProblemAdminForm

    list_display = ('name', 'divisions_display')
    ordering = ('order',)

    def divisions_display(self, obj):
        return ', '.join(map(str, obj.divisions.all()))


class UploadSubmissionAdmin(admin.ModelAdmin):
    inlines = [
        FileSubmissionInline,
    ]

admin.site.register(Settings, SingletonModelAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Division)
admin.site.register(GradedProblem, GradedProblemAdmin)
admin.site.register(GradedSubmission, GradedSubmissionAdmin)
admin.site.register(UploadProblem, UploadProblemAdmin)
admin.site.register(UploadSubmission, UploadSubmissionAdmin)
