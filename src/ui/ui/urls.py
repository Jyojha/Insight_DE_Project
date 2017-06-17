"""ui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.contrib import admin
from views import index, find_path, matching_streets, intersecting_streets

urlpatterns = [

    #when the website address is passed in the browser, it handles the default page
    url(r'^$', index),
    #enter source street
    url(r'^api/matching_streets/$', matching_streets),
    #enter intersecting street
    url(r'^api/intersecting_streets/$', intersecting_streets),
    #finding the route between source and destination entered
    url(r'^api/find_path/$', find_path),


]
