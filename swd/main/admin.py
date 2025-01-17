from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.shortcuts import redirect
from django.utils.html import format_html
import urllib
from django.http import HttpResponseRedirect, HttpResponse
import datetime
from .models import *
from calendar import monthrange
from import_export import resources
from import_export.formats import base_formats
from import_export.admin import ExportActionModelAdmin, ExportMixin, ImportExportModelAdmin
from .resources import ItemBuyResource, TeeBuyResource, MessOptionResource, StudentResource, HostelPSResource, DayPassResource, BonafideResource, LeaveResource  


models = [
    Warden,
    Staff,
    DayScholar,
    CSA,
    LateComer,
    MessOptionOpen,
    Transaction,
    MessBill,
    TeeAdd,
    ItemAdd,
    HostelSuperintendent,
    Notice,
    FileAdd,
    AntiRagging,
    DueCategory,
    DuesPublished,
    Security
]

@admin.register(HostelPS)
class HostelPSAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ['student__name', 'student__bitsId']
    list_display = ['student', 'hostel', 'room']
    list_filter = ['hostel']
    resource_class = HostelPSResource

    def get_export_formats(self):
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ['title', 'hostel']
    list_filter = ['hostel']

@admin.register(VacationDatesFill)
class VacationDatesFillAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_display = ['description', 'dateOpen', 'dateClose']

@admin.register(Disco)
class DiscoAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ['student__bitsId', 'student__name']

    def get_export_formats(self):
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

@admin.register(DayPass)
class DayPassAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ['student__bitsId', 'student__name']
    resource_class = DayPassResource

    def get_export_formats(self):
        formats = (
          base_formats.XLS,
          )
        return [f for f in formats if f().can_export()]


@admin.register(Bonafide)
class BonafideAdmin(ExportMixin,admin.ModelAdmin):
    search_fields = ['reason','otherReason', 'reqDate','student__name','student__bitsId']
    list_display = (
        'id',
        'student',
        'reason', 
        'reqDate',
        'printed',
        'status',
        'bonafide_actions',
    )
    resource_class = BonafideResource
    list_filter = ('status',)
    def get_url(self, pk):
        url = '/bonafide/' + str(Bonafide.objects.get(pk=pk).id)
        return url

    def bonafide_actions(self, obj):
        return format_html  (
            '<a class="button" href="{}" target="blank_">Print</a>&nbsp;',
            self.get_url(obj.pk),
        )
    bonafide_actions.short_description = 'Bonafide Actions'
    bonafide_actions.allow_tags = True

    def get_export_formats(self):
        formats = (
          base_formats.XLS,
          )
        return [f for f in formats if f().can_export()]

def exportmessbill_xls(modeladmin, request, queryset):
    select = [ i.student.bitsId for i in queryset]
    return HttpResponseRedirect("/messbill/?ids=%s" % (",".join(select)))
exportmessbill_xls.short_description = u"Export Mess Bill"


def update_cgpa(modeladmin, request, queryset):
    return redirect('import_cgpa')
update_cgpa.short_description = u"Update CGPAs with Excel File"

def add_new_students(modeladmin, request, queryset):
    return redirect('add_new_students')
add_new_students.description = u"Add New Students from Excel"

def delete_students(modeladmin, request, queryset):
    return redirect('delete_students')
delete_students.description = u"Delete Students from Excel"

@admin.register(Student)
class StudentAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ['name', 'bitsId', 'user__username']
    list_display = ['name', 'bitsId', 'gender', 'phone']
    actions = [add_new_students, delete_students ]
    resource_class = StudentResource
    def get_export_formats(self):
        formats = (
          base_formats.XLS,
          )
        return [f for f in formats if f().can_export()]


@admin.register(TeeBuy)
class TeeBuyAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = TeeBuyResource
    search_fields = ['tee__title']  


@admin.register(ItemBuy)
class ItemBuyAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = ItemBuyResource  
    search_fields = ['item__title']


@admin.register(MessOption)
class MessOptionAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = MessOptionResource
    search_fields = ['mess','monthYear', 'student__bitsId', 'student__name']
    list_display = ('student', 'mess', 'monthYear')
    list_filter = ('mess','monthYear')

    
@admin.register(Leave)
class LeaveAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['student__name', 'student__bitsId','dateTimeStart','id', 'student__user__username', 'reason']
    actions = [exportmessbill_xls, ]
    list_display = ('student', 'reason','approved','dateTimeStart')
    list_filter = ('student', 'reason')

    resource_class = LeaveResource
    def get_export_formats(self):
        formats = (
          base_formats.XLS,
          )
        return [f for f in formats if f().can_export()]

@admin.register(Due)
class DueAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    search_fields = ['student__name','student__bitsId','amount','due_category__name','description','date_added']
    list_display = ('student', 'amount','due_category','date_added',)

    def get_export_formats(self):
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

admin.site.register(models)