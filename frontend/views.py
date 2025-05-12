from django.shortcuts import render,get_object_or_404,redirect
from backend.models import *
from django.http import Http404
from django.conf import settings
import os
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
# Create your views here.

def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = authenticate(request, rollno=username, password=password)
            if user is not None:
                user.backend = 'backend.backends.RollNumberBackend'
                login(request,user)
                response = redirect('home')
                response.set_cookie('username', username)  # Lasts until browser is closed
                return response
            else:
                messages.error(request, "Incorrect username or password.")  # Add flash message
        except Lms_Users.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request,'frontend/login.html')
    

@login_required(login_url='/')
def home(request):
    courses = Course.objects.all()
    username = request.COOKIES.get('username')
    departments = Department.objects.all()
    videos=Video.objects.all()
    context = {
        'courses': courses,
        'departments': departments,
        'videos':videos,
        'username':username,
    }
    response = render(request, 'frontend/home_page.html', context) 
    return response


@login_required(login_url='/')
def about(request):
    return render(request,'frontend/about.html')

@login_required(login_url='login_page')
def profile(request):
    username = request.COOKIES.get('username')
    if username:
       student = Lms_Users.objects.get(rollno=username)
    else:
         student=None
    return render(request,'frontend/profile.html',{'student':student})


def logout_page(request):
    logout(request)
    return redirect('/') 

@login_required(login_url='login_page')
def course_details(request,course_name):
    videos = Video.objects.all()
    return render(request,'frontend/fetch_course_videos.html',{'videos':videos})


@login_required(login_url='/')
def fetch_course_videos(request, course_name):
    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos', course_name)
    video_files = []

    # Check if the folder exists
    if os.path.exists(video_dir):
        for file in os.listdir(video_dir):
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):  # Add any other video extensions you want to support
                video_files.append(os.path.join('videos', course_name, file))  # Store relative path
    else:
        raise Http404("Folder does not exist.")

    # Fetch the course object
    course = get_object_or_404(Course, course_name=course_name)

    # Fetch videos related to the selected course
    videos = Video.objects.filter(course_name=course)

    context = {
        'videos': videos,  # This now holds the relative paths for rendering
        'course': course,
        'title': course_name,
    }

    return render(request, 'frontend/fetch_course_videos.html', context)

@login_required(login_url='/')
def track_video_views(request):
    if request.method == "POST":
        video_id = request.POST.get('video_id')
        video = get_object_or_404(Video, id=video_id)
        video.views += 1
        video.save()
        return JsonResponse({'status': 'success', 'views': video.views})
    return JsonResponse({'status': 'fail'}, status=400)

@login_required(login_url='/')
def like_video(request):
    if request.method == "POST":
        video_id = request.POST.get('video_id')
        video = get_object_or_404(Video, id=video_id)
        video.likes += 1
        video.save()
        return JsonResponse({'status': 'success', 'likes': video.likes})
    return JsonResponse({'status': 'fail'}, status=400)


@login_required(login_url='/')
def verifypassword(request):
    if request.method == 'POST':
        old_password = request.POST['oldPassword']
        username = request.COOKIES.get('username')  
        try:
            user = Lms_Users.objects.get(rollno=username)
            if user.check_password(old_password):  # Check if the old password is correct
                return render(request, 'frontend/changepassword.html')
            else:
                messages.error(request, "Old password is incorrect.")  # Add flash message
        except Lms_Users.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, 'frontend/verifypassword.html')

@login_required(login_url='/')
def changepassword(request):
    if request.method == 'POST':
        newpassword = request.POST['newPassword']
        confirmpassword = request.POST['confirmPassword']

        username = request.COOKIES.get('username')
        try:
            user = Lms_Users.objects.get(rollno=username)
            if newpassword == confirmpassword:
                # Save the new password
                user.set_password(newpassword)
                user.save()
                messages.success(request, "Password changed successfully.")
                logout(request)
                return redirect('/logout_page') 
            else:
                messages.error(request, "Passwords do not match.")
        except Lms_Users.DoesNotExist:
            messages.error(request, "User not found.")

    return render(request, 'frontend/changepassword.html')
