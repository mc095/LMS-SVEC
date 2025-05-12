from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import *
from .models import *
import os
from django.conf import settings
import pandas as pd
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
import subprocess



def add_video(request):
    form = CustomAdminForm(request.POST, request.FILES)

    if request.method == 'POST':
        if form.is_valid():
            video_file = request.FILES['video_file']
            dept_id = form.cleaned_data['dept']
            course_name = form.cleaned_data['course_name']
            description = form.cleaned_data['description']

            # Check for missing data
            if dept_id is None or course_name is None or description is None:
                return HttpResponse("Missing POST data.")

            course_name_str = str(course_name)
            upload_directory = os.path.join(settings.MEDIA_ROOT, 'videos', course_name_str)

            # Create the directory if it doesn't exist
            os.makedirs(upload_directory, exist_ok=True)

            # Save the video file
            video_path = os.path.join(upload_directory, video_file.name)
            with open(video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)

            # Create an HLS directory named after the video title
            video_title = form.cleaned_data['title'].replace(" ", "_")  # Replace spaces for folder name
            hls_directory_name = f"{video_title}_HLS"
            hls_directory = os.path.join(upload_directory, hls_directory_name)

            # Create the HLS directory
            os.makedirs(hls_directory, exist_ok=True)

            # Create HLS segments using ffmpeg
            hls_command = [
                'ffmpeg',
                '-i', video_path,
                '-codec:v', 'libx264',
                '-codec:a', 'aac',
                '-hls_time', '10',
                '-hls_playlist_type', 'vod',
                '-hls_segment_filename', os.path.join(hls_directory, 'segment%03d.ts'),
                os.path.join(hls_directory, 'playlist.m3u8')
            ]

            try:
                subprocess.run(hls_command, check=True)
            except subprocess.CalledProcessError as e:
                return HttpResponse(f"FFmpeg error: {str(e)}")
            except Exception as e:
                return HttpResponse(f"General error: {str(e)}")

            # Save video instance details
            video_instance = Video(
                title=form.cleaned_data['title'],
                video_file=os.path.join('videos', course_name_str, video_file.name),
                dept=Department.objects.get(dept=dept_id),
                course_name=Course.objects.get(course_name=course_name),
                description=description,
                hls_path=os.path.join('videos', course_name_str, hls_directory_name, 'playlist.m3u8').replace('\\', '/')  # Save HLS playlist path
            )
            video_instance.save()

            return redirect('admin:backend_video_changelist')

    return render(request, 'upload.html', {'form': form})


def course_upload(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)  # Include request.FILES
        if form.is_valid():
            course = form.save(commit=False)  # Do not save yet
            
            # Handle the image upload
            if request.FILES.get('image'):
                course.image = request.FILES['image'].read()  # Read the image as binary data
            
            course.save()  # Now save the instance
            return redirect('admin')  # Redirect after success
    else:
        form = CourseForm()
    
    return render(request,'couse_uplod.html',{'form':form})

def custom_admin_view_add(request):
    # Your custom view logic here
    return render(request, 'custom_view_template.html')


@staff_member_required  
def custom_admin_view(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["excel_file"]
            try:
                df = pd.read_excel(excel_file)
                for index, row in df.iterrows():
                    user = Lms_Users(
                        rollno=row['Htno'],  
                        name=row['Name'],
                        branch=row['Branch'],
                    )
                    # Set the Aadhar number as the password, but don't store it directly
                    if pd.isna(row['AadharNumber']):
                        row['AadharNumber']=row['Htno']
                    user.set_password(str(row['AadharNumber']))  # AadharNumber column is used as password
                    user.save()
                    print(row['Htno']," ",str(row['AadharNumber']))
                return redirect('admin:backend_lms_users_changelist')
            except Exception as e:
                return HttpResponse(f"Error processing file: {str(e)}")
    else:
        form = ExcelUploadForm()

    return render(request, "admin/custom_view_template.html", {"form": form})


@receiver(post_delete, sender=Video)
def delete_video_file(sender, instance, **kwargs):
    if instance.video_file:
        video_path = instance.video_file.name
        print(f"Deleting file via signal: {video_path}")
        if default_storage.exists(video_path):
            default_storage.delete(video_path)
        else:
            print(f"File not found: {video_path}")


@receiver(post_delete, sender=Course)
def delete_course_related_files(sender, instance, **kwargs):
    # Deleting the course videos folder in media/videos/{course_name}
    video_folder_path = os.path.join('media', 'videos', instance.course_name)
    if os.path.exists(video_folder_path):
        try:
            shutil.rmtree(video_folder_path)
            print(f"Deleted video folder: {video_folder_path}")
        except Exception as e:
            print(f"Error deleting video folder {video_folder_path}: {e}")
    if instance.image and os.path.exists(instance.image.path):
        try:
            os.remove(instance.image.path)
            print(f"Deleted image: {instance.image.path}")
        except Exception as e:
            print(f"Error deleting image {instance.image.path}: {e}")