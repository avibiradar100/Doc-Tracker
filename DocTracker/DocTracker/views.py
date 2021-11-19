import pyrebase
import os
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import auth
from django.views import generic
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from collections import OrderedDict
import datetime
import time
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# for report 
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter


config = {
    "apiKey": "AIzaSyC3DKMArlBjbnv2l77aUUsgAi_-bR9bFD8",
    "authDomain": "wce-doc-tracker.firebaseapp.com",
    "databaseURL": "https://wce-doc-tracker-default-rtdb.firebaseio.com",
    "projectId": "wce-doc-tracker",
    "storageBucket": "wce-doc-tracker.appspot.com",
    "messagingSenderId": "127465159856",
    "appId": "1:127465159856:web:1f4f662785411fc525cf75"
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth()
database = firebase.database()


class landingPage(View):

    def get(self, request, template_name='landingPage.html'):
        pName = database.child("Data").child('Name').get().val()
        pRoll = database.child("Data").child('Roll').get().val()
        pStd = database.child("Data").child('std').get().val()
        try:
            message = {'message': 'message'}
            message['message'] = pName+' '+pRoll+' '+pStd
            print(message)
        except:
            message = {'message': 'message'}
            message['message'] = 'nothing'
        return render(request, template_name)

    # fetch status of document 
    def post(self, request, template_name='landingPage.html'):
        token = request.POST.get('token')
        billTytpe = request.POST.get('billType')

        if billTytpe == "Bill":
            data = database.child('Documents').child(
                "Bill").child(token).get().val()
        elif billTytpe == "Report":
            data = database.child('Documents').child(
                "Report").child(token).get().val()
        elif billTytpe == "Proposal":
            data = database.child('Documents').child(
                "Proposals").child(token).get().val()
        else:
            data = database.child('Documents').child(
                "Requests").child(token).get().val()

        print(data)

        try:
            print("In try of post")
            msg = {}
            msg['token'] = token
            od = data
            print(od)
            status = []
            x = 1
            for val in od.values():
                s = ""

                for k, v in val.items():
                    # print(k, v)

                    if x % 2 == 0:
                        # utc_time = datetime.datetime.fromtimestamp(v / 1000.0, tz=datetime.timezone.utc)
                        utc_time = datetime.datetime.fromtimestamp(
                            v, tz=datetime.timezone.utc)
                        # msg[k]=utc_time
                        print(utc_time)
                        s = s+str(utc_time)+"  \n"
                        # status.append(utc_time)
                        print("===============")
                    else:
                        msg[k] = v
                        print(k, v)
                        # status.append(v)
                        s = s+str(v) + " at  "
                        print("-=-=-=-=-=-=-=-=-=-")
                    x = x+1
                status.append(s)
                print(s)

            msg['status'] = status
            # status.clear()
            return render(request, 'landingPage.html', msg)
        except:
            msg = {}
            msg['token'] = token
            # msg['error_message'] = "Failed fetch"
            return render(request, template_name, msg)


class about(View):
    def get(self, request, template_name='about.html'):
        return render(request, template_name)

# Staff report generating 
class report(View):
    def get(self, request, template_name='landingPage.html'):
        return render(request, template_name)

     # fetch report of user  
    # def post(self, request, template_name='report.html'):
    def post(self, request, template_name='report.html'):
        print("122")
        staffEmail = request.POST.get('staffEmail')
        print(staffEmail)
        staffEmailModified= staffEmail.replace(".","")
        
        data = database.child('staffData').child(
                "mails").child(staffEmailModified).get().val()
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf , pagesize=letter,bottomup=0)

        textob = c.beginText()
        textob.setTextOrigin(inch , inch)
        textob.setFont("Helvetica-Bold" , 20)
        textob.textLine("           Report of "+str(staffEmail))
        textob.textLine("")
        textob.setFont("Helvetica" , 14)
        print(data)
        print("146")
        msg = {}
        try:
            print("In try of report  post")
            
            od = data
            lines=[]
            # print(od)
            status = []
            print(lines)

            for val in od.values():
                status.append(val)
                # print(type(val))
                lines.append(val)
            print("159")
            # lines=[
            #     "I am here 1",
            #     "I am here 2",
            #     "I am here 3"
            # ]
            counter=1
            for line in lines:
                temp=str(line)
                temp=temp[1:-1]
                textob.textLine(str(counter)+")        "+temp)
                textob.textLine()
                counter+=1

            textob.textLine("                       --------------------X--------------------")
            print("162")    

            msg['status'] = status
            # status.clear()

            c.drawText(textob)
            c.showPage()
            c.save()
            buf.seek(0)


            # return render(request, 'report.html', msg)
            print("170")
            return FileResponse(buf , as_attachment=True , filename="report.pdf")

        except:
            
            msg['error'] = "Error in fetching report"
            # msg['error_message'] = "Failed fetch"
            return render(request, template_name, msg)


class StaffWork(View):
    def get(self, request, template_name='staffWork.html'):
        return render(request, template_name)

    def post(self, request, template_name='staffWork.html'):
        print(" Inside staffWork post ")

        token = request.POST.get('token')
        ownerEmail = database.child('Documents').child(
            "Owner").child(token).get().val()
        print(ownerEmail)
        od = ownerEmail
        tempEmail = ""
        docType = ""
        for val in od.values():
            for k, v in val.items():
                if k == "email":
                    tempEmail = v
                if k == "docType":
                    docType = v
                    

        ownerEmail = tempEmail
        print(ownerEmail)
        staffEmail=''
        idtoken = request.session['uid']
        a = authe.get_account_info(idtoken)
        print(a)
        a = a['users']
        print(a)
        a = a[0]
        print(a)
        staffEmail = a['email']
        checkUser = staffEmail.split('@')[0]
        checkDept = checkUser[:len(checkUser)-2]
        msg1 = {}
        try:
            msg1["token"]=token
            message = request.POST.get('message')
            decision = request.POST['decision']

            print(token)
            print(message)
            print(decision)
            import time
            from datetime import datetime, timezone
            import pytz
            print("line 144")
            tz = pytz.timezone('Asia/Kolkata')
            time_now = datetime.now(timezone.utc).astimezone(tz)
            if decision == "accept":
                
                message=str(staffEmail)+" -> "+message+" -> [ ACCEPTED ]"
                print(staffEmail)

                a = a['localId']
                print("line 140")
                
                print("line 147")
                data = {
                    "By": message,
                    "at": int(time.mktime(time_now.timetuple()))
                }
                # teknathk1@gmail.com     teknath
                print("line 153")
                
                print("CheckDept : "+checkDept)
                
                # token=int(token)
                print("line 163")
                msg1["savedToDB"]="Not yet"
                flag= False

                # idtoken = request.session['uid']
                # a = authe.get_account_info(idtoken)
                # a = a['users']
                # a = a[0]
                
                # a = a['localId']

                try:
                    print("In try of 273")
                    tz = pytz.timezone('Asia/Kolkata')
                    time_now = datetime.now(timezone.utc).astimezone(tz)
                    millis = int(time.mktime(time_now.timetuple()))
                    staffData={}
                    staffData["docToken"]=token
                    staffData["date"] = millis
                    rootEmail=staffEmail.replace(".","")
                    database.child("staffData").child("mails").child(rootEmail).push(staffData)
                    
                except :
                    print("error in staffData")


                if checkDept == "bill" and docType=="Bill":
                    print("Bill")
                    fToken = database.child(
                        "Documents").child('Bill').get().val()
                    print(fToken)
                    database.child('Documents').child("Bill").child(
                        token).push(data)
                    msg1["savedToDB"]="Yes saved to Bill"

                    print("Bill  ok ")
                    flag = True
                elif checkDept == "report" and docType=="Report":
                    print("Report")
                    fToken = database.child("Documents").child(
                        'Report').get().val()
                    print(fToken)
                    database.child('Documents').child("Report").child(
                        token).push(data)
                    msg1["savedToDB"]="Yes saved to Report"
                    print("Report  ok ")
                    flag = True
                elif checkDept == "request"  and docType=="Request":
                    print("Request")
                    fToken = database.child("Documents").child(
                        'Requests').get().val()
                    print(fToken)
                    database.child('Documents').child("Requests").child(
                        token).push(data)
                    msg1["savedToDB"]="Yes saved to Request"
                    print("Request  ok ")
                    flag = True
                elif checkDept == "proposal" and docType=="Proposal":
                    print("Proposal")
                    fToken = database.child("Documents").child(
                        'Proposal').get().val()
                    print(fToken)
                    database.child('Documents').child("Proposals").child(
                        token).push(data)
                    msg1["savedToDB"]="Yes saved to Proposals"
                    print("Proposal  ok ")
                    flag = True
                else:
                    msg1["savedToDB"]="Failed | Acses from wrong account  | Token not exists ."
                    print("Fail to push /  token not exists")

                print("***Status Updated   ->  "+token)

                if message  and flag:
                    message = 'From WCE Doc Tracker . \n Token No. ' + \
                        str(token) + '\n'+message+' from Desk ' + \
                        staffEmail + '\n' + " STATUS : In process "
                    print(message)
                    send_mail(
                        'WCE Doc Tracker ',
                        message,
                        'farookdio72@gmail.com',
                        [ownerEmail],

                    )

                # print("--------Sent--------")
                msg1["status"]="Accepted previous doc"
                return render(request, template_name,msg1)
            else:
                message=str(staffEmail)+" -> "+message+" -> [ REJECTED ]"
                data = {
                    "By": message,
                    "at": int(time.mktime(time_now.timetuple()))
                }
                if checkDept == "bill" and docType=="Bill":
                    database.child('Documents').child("Bill").child(
                        token).push(data)
                elif checkDept == "report" and docType=="Report":
                    database.child('Documents').child("Report").child(
                        token).push(data)
                    flag = True
                elif checkDept == "request"  and docType=="Request":
                    
                    database.child('Documents').child("Requests").child(
                        token).push(data)
                    flag = True
                elif checkDept == "proposal" and docType=="Proposal":
                    database.child('Documents').child("Proposals").child(
                        token).push(data)
                    flag = True
                else:
                    msg1["savedToDB"]="Failed | Acses from wrong account  | Token not exists ."
                    print("Fail to push /  token not exists")

                print("***Status Updated   ->  "+token)
                
                msg1["status"]="Rejected previous doc"
                message = 'From WCE Doc Tracker . \n Token No. ' + \
                    str(token) + '\n'+message+' from ' + staffEmail+ '\n' + " STATUS : Rejected "
                print(message)


                send_mail(
                    'WCE Doc Tracker ',
                    message,
                    'farookdio72@gmail.com',
                    [ownerEmail],

                )
                return render(request, template_name,msg1)
        except:
            print("-----------Not sent--------------")
            err = {}
            # err['error_message1'] = "Account with this Username or Email already exists."
            err['error_message1'] = "Fails to send email message."
            # err['error_message2'] = "Password length must be atleast 6 ."
            return render(request, 'firstClerk.html', err)


class StaffCommonPage(View):
    def get(self, request, template_name='staffLandingPage.html'):
        return render(request, template_name)

# login for all staff common class
class login(View):
    def get(self, request, template_name='login.html'):
        return render(request, template_name)

    def post(self, request, template_name='login.html'):
        email = request.POST.get('email')
        password = request.POST.get('password')
        checkMe = email.split('@')[0]
        checkMe = checkMe[len(checkMe)-2:]
        print(checkMe)
        try:
            if checkMe == "k1":
                user = authe.sign_in_with_email_and_password(email, password)
                print(user)
                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                msg = {}
                msg['designation'] = "Desk 0 "
                msg['email'] = email
                msg['session_id'] = session_id
                msg['local_id'] = user['localId']
                return render(request, 'firstClerk.html', msg)
            elif checkMe == "d1":
                user = authe.sign_in_with_email_and_password(email, password)
                print(user)
                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                msg = {}
                msg['designation'] = "Desk 1"
                msg['email'] = email
                msg['session_id'] = session_id
                msg['local_id'] = user['localId']
                return render(request, 'desk1.html', msg)
            elif checkMe == "d2":
                user = authe.sign_in_with_email_and_password(email, password)
                print(user)
                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                msg = {}
                msg['designation'] = "Desk 2"
                msg['email'] = email
                msg['session_id'] = session_id
                msg['local_id'] = user['localId']
                return render(request, 'desk2.html', msg)
            elif checkMe == "d3":
                user = authe.sign_in_with_email_and_password(email, password)
                print(user)
                session_id = user['idToken']
                request.session['uid'] = str(session_id)
                msg = {}
                msg['designation'] = "Desk 3"
                msg['email'] = email
                msg['session_id'] = session_id
                msg['local_id'] = user['localId']
                return render(request, 'desk3.html', msg)
            else:
                raise ValueError("That is not a valid User!")
        except:
            err = {}
            err['error_message'] = "Invalid credentials"
            return render(request, 'login.html', err)


def logout_user(request):
    auth.logout(request)
    message = {}
    message['loggedOut'] = "Successfully Logged Out"
    return render(request, 'login.html', message)


class signup(View):
    def get(self, request, template_name='signup.html'):
        return render(request, template_name)

    def post(self, request, template_name='signup.html'):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phoneNumber = request.POST.get('phoneNumber')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = authe.create_user_with_email_and_password(email, password)
            uid = user['localId']
            data = {"First_name": first_name,
                    "Last_name": last_name,
                    "email": email,
                    "phoneNumber": phoneNumber,
                    "status": "1"}
            database.child("users").child(uid).child("details").set(data)
            return render(request, 'login.html')
        except:
            err = {}
            err['error_message1'] = "Account with this Username or Email already exists."
            err['error_message2'] = "Password length must be atleast 6 ."
            return render(request, template_name, err)

# @login_required(login_url="/login/")


class create(View):

    def get(self, request, template_name='create.html'):
        return render(request, template_name)

    def post(self, request, template_name='login.html'):
        import time
        from datetime import datetime, timezone
        import pytz
        try:
            tz = pytz.timezone('Asia/Kolkata')
            time_now = datetime.now(timezone.utc).astimezone(tz)
            millis = int(time.mktime(time_now.timetuple()))
            print(str(millis))
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phoneNumber = request.POST.get('phoneNumber')
            email = request.POST.get('email')
            print("132")
            billCode = request.POST['billType']

            print("line 404")
            print(billCode)
            msg1 = {}
            msg1['email'] = email
            msg1['phoneNumber'] = phoneNumber
            # password = request.POST.get('password')
            idtoken = request.session['uid']
            a = authe.get_account_info(idtoken)

            a = a['users']
            a = a[0]
            clerkEmail = a['email']
            # clerkName=a['First_name']
            a = a['localId']
            print("line 418")
            # msg1['local_id'] = a['localId']
            print(str(a))
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phoneNumber": phoneNumber,
                "docType": billCode,
                "timeStamp": millis,
            }
            print("line 150")
            database.child('users').child(a).child(
                'reports').child(millis).set(data)
          
            data1 = {
                "By": clerkEmail,
                "at": millis,
            }
            # database.child('Documents').child("Bill").child(millis).push(data1)
            print("line 164")
            # print(billCode )
            if billCode == "Bill":
                database.child('Documents').child("Bill").child(
                    millis).child("data").push(data1)
                print("Bill")
            elif billCode == "Report":
                database.child('Documents').child(
                    "Report").child(millis).push(data1)
                print("Report")
            elif billCode == "Proposal":
                database.child('Documents').child(
                    "Proposals").child(millis).push(data1)
                print("Proposal")
            elif billCode == "Request":
                database.child('Documents').child(
                    "Requests").child(millis).push(data1)
                print("Request")

            database.child('Documents').child(
                "Owner").child(millis).push(data)
            print("***Saved*****")

            message = 'Welcome to doc tracker . \n Token No. '+str(millis)
            print(message)
            send_mail(
                'WCE Doc Tracker ',
                message,
                'farookdio72@gmail.com',
                [email],

            )

            print("--------Sent--------")

            return render(request, 'create.html', msg1)
        except:
            print("-----------Not sent--------------")
            err = {}
            # err['error_message1'] = "Account with this Username or Email already exists."
            err['error_message1'] = "Fails to send email message."
            # err['error_message2'] = "Password length must be atleast 6 ."
            return render(request, 'firstClerk.html', err)
