"""codelm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^problem/(?P<problem_id>(g|u)[0-9]+)$', views.problem, name='problem'),
    url(r'^problem/(?P<problem_id>(g|u)[0-9]+)/submit$', views.api_submit, name='submit'),
    url(r'^submission/(?P<submission_id>(g|u)[0-9]+)$', views.submission, name='submission'),

    url(r'^api/logout$', views.api_logout, name='api_logout'),
    url(r'^api/edit-submission$', views.api_edit_submission, name='api_edit_submission'),
    url(r'^api/widget$', views.api_widget, name='api_widget'),
    url(r'^api/file/(?P<file_id>[0-9]+)$', views.api_file, name='api_file'),
]
