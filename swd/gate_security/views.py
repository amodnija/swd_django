from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InOut, WeekendPass
from main.models import Leave, DayPass, Student, VacationDatesFill, HostelPS, LateComer
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from main.templatetags.main_extras import is_hostelsuperintendent, is_warden, is_security, get_base_template
import swd.config as config
from datetime import date, datetime, timedelta, time
from dateutil import rrule, parser
from django.core.exceptions import MultipleObjectsReturned
from django.contrib import messages
import xlwt

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def gate_security(request):
    context = {}
    errors = []
    if request.method == 'POST':
        if request.POST.get("form_type") == 'formOne':
            #The first form - In the inout tab when the guard enters bitsID and all the active
            # leaves etc are shown for a particular student.
            username = request.POST.get('username')
            try:
                student = Student.objects.get(bitsId=username)
                errors = []
            except Student.DoesNotExist:
                student = None
                errors.append("Please enter correct BITS ID")

            f=0
            try:
                try:
                    f=1
                    inout = InOut.objects.get(student__bitsId=username)
                except (IndexError, MultipleObjectsReturned):  
                    f=2
                    inout = InOut.objects.filter(student__bitsId=username).order_by('-id')[0]
            except InOut.DoesNotExist:
                inout = None

            try:
                daypass = DayPass.objects.get(
                        approved__exact=True,
                        dateTime__date__exact=datetime.today().date(),
                        student__bitsId=username,
                        claimed=False
                )
            except DayPass.DoesNotExist:
                daypass = None

            try:
                t = time(0,0)
                t1 = time(23,59)
                d = date.today()
                leave = Leave.objects.get(
                        dateTimeEnd__gte=datetime.combine(d,t),
                        dateTimeStart__lte=datetime.combine(d,t1),
                        student__bitsId=username,
                        claimed=False,
                        approved=True
                )
            except Leave.DoesNotExist:
                leave = None
            
            try:
                weekendpass = WeekendPass.objects.get(
                        student__bitsId=username,
                        expiryDate__gte=datetime.today().date(),
                        approved=True)
            except WeekendPass.DoesNotExist:
                weekendpass = None

            try:
                vacationdates = VacationDatesFill.objects.get(
                                allowDateAfter__lte=datetime.today().date(),
                                allowDateBefore__gte=datetime.today().date()
                )
            except MultipleObjectsReturned:
                vacationdates = VacationDatesFill.objects.filter(
                                allowDateAfter__lte=datetime.today().date(),
                                allowDateBefore__gte=datetime.today().date()
                ).first()                
            except VacationDatesFill.DoesNotExist:
                vacationdates = None
            print(vacationdates)

            last5 = []
            if f>0:
                if f==1:
                    last5.append(inout)
                else:
                    for io in InOut.objects.filter(student__bitsId=username).order_by('-id'):
                        if len(last5)<5:
                            last5.append(io)

            print(last5)

            context = {
                'last5' : last5,
                'student': student,
                'leave': leave,
                'daypass': daypass,
                'weekendpass': weekendpass,
                'inout': inout,
                'errors': errors,
                'vacationdates': vacationdates,
            }
            return render(request, "gate_security.html", context)

        elif request.POST.get("form_type") == 'formTwo':
            #The guard records an inout activity of the student
            username = request.POST.get('bitsid')
            student = Student.objects.get(bitsId=username)
            place = request.POST.get('place')
            leave_check = request.POST.get('leave_check')
            daypass_check = request.POST.get('daypass_check')
            incampus_check = request.POST.get('incampus_check')
            weekendpass_check = request.POST.get('weekendpass_check')
            vacation_check = request.POST.get('vacation_check')

            try:
                try:
                    inout = InOut.objects.get(student__bitsId=username)
                except (IndexError, MultipleObjectsReturned):    
                    inout = InOut.objects.filter(student__bitsId=username).order_by('-id')[0]
            except InOut.DoesNotExist:
                inout = None

            t = time(0,0)
            t1 = time(23,59)
            d = date.today()
            try:
                leave = Leave.objects.get(
                            (
                                Q(dateTimeEnd__gte=datetime.combine(d,t)) &
                                Q(dateTimeStart__lte=datetime.combine(d,t1)) &
                                Q(claimed=False) & Q(approved=True)
                            ) |
                            Q(inprocess=True),
                            student__bitsId=username
                )
            except Leave.DoesNotExist:
                leave = None

            try:
                daypass = DayPass.objects.get(
                        (
                            Q(approved__exact=True) &
                            Q(dateTime__date__exact=datetime.today().date()) &
                            Q(claimed=False)
                        ) |
                        Q(inprocess=True),
                        student__bitsId=username
                )
            except DayPass.DoesNotExist:
                daypass = None

            try:
                weekendpass = WeekendPass.objects.get(
                        student__bitsId=username,
                        expiryDate__gte=datetime.today().date(),
                        approved=True)
            except WeekendPass.DoesNotExist:
                weekendpass = None

            try:
                t = time(0,0)
                d = date.today()
                vacationdates = VacationDatesFill.objects.get(
                                allowDateAfter__gte=datetime.combine(d,t),
                )
            except VacationDatesFill.DoesNotExist:
                vacationdates = None

            late = False

            if inout:
                #We have an existing inout object created of the student
                if inout.inCampus == True:
                    # Student is leaving campus
                    inout.place = place
                    inout.inCampus = False
                    inout.outDateTime = datetime.now()
                    inout.inDateTime = inout.inDateTime
                    inout2 = InOut(
                            student=student,
                            place=inout.place,
                            inDateTime=inout.inDateTime,
                            outDateTime=inout.outDateTime,
                            inCampus=inout.inCampus,
                            onLeave=inout.onLeave,
                            onDaypass=inout.onDaypass,
                            onVacation=inout.onVacation
                    )
                    inout2.save()
                    inout.save()

                    if leave_check:
                        inout.onLeave = True
                        leave.inprocess = True
                        if leave.comment == 'Vacation':
                            inout.onVacation = True
                        inout.save()
                        leave.save()

                    elif daypass_check:
                        inout.onDaypass = True
                        inout.save()
                        daypass.inprocess = True
                        daypass.save()

                    elif weekendpass_check:
                        inout.onWeekendPass = True
                        inout.save()

                    elif vacation_check:
                        inout.onVacation = True
                        inout.save()

                else:
                    #Student is coming back in campus
                    inout.place = place
                    inout.inCampus = True
                    inout.inDateTime = datetime.now()
                    inout.outDateTime = inout.outDateTime
                    if inout.onLeave == True:
                        inout.onLeave = False
                        leave.inprocess = False
                        leave.claimed = True
                        leave.save()
                        inout.save()
                    if inout.onDaypass == True:
                        inout.onDaypass = False
                        daypass.inprocess = False
                        daypass.claimed = True
                        daypass.save()
                        inout.save()
                    if inout.onVacation == True:
                        inout.onVacation =False
                    
                    inout2 = InOut(
                            student=student,
                            place=inout.place,
                            inDateTime=inout.inDateTime,
                            outDateTime=inout.outDateTime,
                            inCampus=inout.inCampus,                            
                            onLeave=inout.onLeave,
                            onDaypass=inout.onDaypass,
                            onVacation=inout.onVacation
                    )
                    inout2.save()
                    inout.save()
                    dt_2 = datetime(2022, 6, 27, 22, 30, 00)
                    if inout.inDateTime.time() > dt_2.time():
                        late = True
                        la = LateComer(
                            student=student,
                            dateTime = inout.inDateTime
                        )
                        la.save()
                        
            else:
                #Creating an inout object of the student in case it was not existing
                inout = InOut(
                            student=student,
                            place=place,
                            inDateTime=datetime.now(),
                            outDateTime=datetime.now(),
                            inCampus=False,
                            onLeave=False,
                            onDaypass=False,
                            onVacation=True
                )
                if not incampus_check:
                    #If the student is leaving campus
                    inout.inCampus=False
                    inout.outDateTime = datetime.now()
                    inout.inDateTime = None
                    inout.save()

                    if leave_check:
                        inout.onLeave = True
                        if leave.comment == 'Vacation':
                            inout.onVacation = True
                        inout.save()
                        leave.inprocess = True
                        leave.save()

                    if daypass_check:
                        inout.onDaypass = True
                        inout.save()
                        daypass.inprocess = True
                        daypass.save()
                    if vacation_check:
                        inout.onVacation = True
                        inout.save()

                else:
                    #If the student is coming back in campus
                    inout.place=place
                    inout.inCampus=True
                    inout.inDateTime = datetime.now()
                    inout.outDateTime = None
                    if inout.onLeave == True:
                        inout.onLeave = False
                        leave.inprocess = False
                        leave.claimed = True
                        leave.save()
                    if inout.onDaypass == True:
                        inout.onDaypass = False
                        daypass.inprocess = False
                        daypass.claimed = True
                        daypass.save()
                    if inout.onVacation == True:
                        inout.onVacation = False
                    inout.save()
                    dt_2 = datetime(2022, 6, 27, 22, 30, 00)
                    if inout.inDateTime.time() > dt_2.time():
                        late = True
                        la = LateComer(
                            student=student,
                            dateTime = inout.inDateTime
                        )
                        la.save()
            context = {
                'late' : late,
                'student': student,
                'inout': inout,
                'success': True,
            }
            return render(request, "gate_security.html", context)
    return render(request, "gate_security.html", context)


@user_passes_test(lambda u: u.is_superuser or is_security(u))
def dash_security_leaves(request):
    t = time(0,0)
    t1 = time(23,59)
    d = date.today()
    approved_leaves = Leave.objects.filter(approved__exact=True, dateTimeEnd__gte=datetime.combine(d,t), dateTimeStart__lte=datetime.combine(d,t1)).order_by('-dateTimeStart')
    context = {'leaves' : approved_leaves}
    return render(request, "dash_security.html", context)


@user_passes_test(lambda u: u.is_superuser or is_security(u))
def dash_security_daypass(request):
    t = time(0,0)
    t1 = time(23,59)
    d = date.today()
    approved_daypass = DayPass.objects.filter(approved__exact=True, dateTime__date__exact=datetime.today().date()).order_by('-dateTime')
    context = {'daypasses' : approved_daypass}
    return render(request, "daypasses_security.html", context)

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def in_out(request):
    if not request.POST:
        inout = InOut.objects.filter(inCampus = False, onLeave = False, onDaypass = False).order_by('-outDateTime')

        ioreal = []
        students = []

        for io in inout:
            if HostelPS.objects.get(student = io.student).hostel and InOut.objects.filter(student=io.student).order_by('-id')[0].inCampus==False:
                if io.student not in students:
                    students.append(io.student)
                    ioreal.append(io)
                else:
                    if ioreal[students.index(io.student)].outDateTime < io.outDateTime:
                        ioreal[students.index(io.student)] = io
        context = {
            'inout': ioreal,
        }
        return render(request, "all_in_out.html", context)
    
    # Handle POST request here

    CURRENT_DATE_TIME = datetime.now()
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename=Students-Outside-{CURRENT_DATE_TIME}.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(f"Students Outside")

    heading_style = xlwt.easyxf('font: bold on, height 280; align: wrap on, vert centre, horiz center')
    h2_font_style = xlwt.easyxf('font: bold on')
    font_style = xlwt.easyxf('align: wrap on')

    columns = [
        (u"Name", 6000),
        (u"BITS ID", 6000),
        (u"Contact", 6000),
        (u"Out Date", 3000),
        (u"Out Time", 3000),
        (u"Location", 6000),
        (u"Reason", 3000),
    ]

    # This function is not documented but given in examples of repo
    #     here: https://github.com/python-excel/xlwt/blob/master/examples/merged.py
    # Prototype:
    #     sheet.write_merge(row1, row2, col1, col2, 'text', fontStyle)
    # Write the header in merged cells
    ws.write_merge(0, 0, 0, len(columns)-1, "Students Outside", heading_style)

    ws.write(1, 0, "Generated:", h2_font_style)
    ws.write(1, 1, CURRENT_DATE_TIME.strftime('%d/%b/%Y , %H:%M:%S'), font_style)

    row_num = 2

    # Write all column titles
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], h2_font_style)
        ws.col(col_num).width = columns[col_num][1]

    inouts = InOut.objects.filter(inCampus = False)

    for inout in inouts:
        row_num += 1
        student = inout.student

        out_datetime = parser.parse(str(inout.outDateTime))
        out_date = out_datetime.date().strftime("%d/%m/%Y")
        out_time = out_datetime.time().strftime("%H:%M")

        # Get reason for inout
        possible_reasons = [(inout.onLeave, "Leave"), (inout.onDaypass, "Daypass"), (inout.onWeekendPass, "WeekendPass"), (inout.onVacation, "Vacation")]
        reason = [i for i in possible_reasons if i[0]]
        reason = reason[0][1] if len(reason) else ""

        row = [student.name, student.bitsId, student.phone, out_date, out_time, inout.place, reason]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    messages.success(request, "Students Outside exported. Download will automatically start.")
    return response

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def defaulters(request):
    if not request.POST:
        late = LateComer.objects.all()
        context = {
            'late': late,
        }
        return render(request, "all_late.html", context)
    
    # Handle POST request here

    CURRENT_DATE_TIME = datetime.now()
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename=Students-Outside-{CURRENT_DATE_TIME}.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(f"Late Comers")

    heading_style = xlwt.easyxf('font: bold on, height 280; align: wrap on, vert centre, horiz center')
    h2_font_style = xlwt.easyxf('font: bold on')
    font_style = xlwt.easyxf('align: wrap on')

    columns = [
        (u"Name", 6000),
        (u"BITS ID", 6000),
        (u"Date", 3000),
        (u"Time", 3000),
    ]

    # This function is not documented but given in examples of repo
    #     here: https://github.com/python-excel/xlwt/blob/master/examples/merged.py
    # Prototype:
    #     sheet.write_merge(row1, row2, col1, col2, 'text', fontStyle)
    # Write the header in merged cells
    ws.write_merge(0, 0, 0, len(columns)-1, "Late comers", heading_style)

    ws.write(1, 0, "Generated:", h2_font_style)
    ws.write(1, 1, CURRENT_DATE_TIME.strftime('%d/%b/%Y , %H:%M:%S'), font_style)

    row_num = 2

    # Write all column titles
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], h2_font_style)
        ws.col(col_num).width = columns[col_num][1]

    late = LateComer.objects.all()

    for la in late:
        row_num += 1
        student = la.student

        out_datetime = parser.parse(str(la.dateTime))
        out_date = out_datetime.date().strftime("%d/%m/%Y")
        out_time = out_datetime.time().strftime("%H:%M")

        row = [student.name, student.bitsId, student.phone, out_date, out_time]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    messages.success(request, "Latecomer list exported. Download will automatically start.")
    return response

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def leave_out(request):
    gte = datetime.combine(
        datetime.today().date(),
        time.min
    )
    inout = InOut.objects.filter(inCampus = False, onLeave = True, onDaypass = False, outDateTime__gte=gte).order_by('-outDateTime')
    context = {
        'inout': inout,
    }
    return render(request, "leave_out.html", context)

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def daypass_out(request):
    gte = datetime.combine(
        datetime.today().date(),
        time.min
    )
    inout = InOut.objects.filter(inCampus = False, onLeave = False, onDaypass = True, outDateTime__gte=gte).order_by('-outDateTime')
    context = {
        'inout': inout,
    }
    return render(request, "daypass_out.html", context)

@user_passes_test(lambda u: u.is_superuser or is_security(u))
def dash_security_weekendpass(request):
    approved_weekend = WeekendPass.objects.filter(
            approved=True,
            expiryDate__gte=datetime.today().date()
    )
    context = {'weekend_pass' : approved_weekend}
    return render(request, "weekend_security.html", context)
