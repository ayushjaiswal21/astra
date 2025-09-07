from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    # Page rendering
    path('', views.course_list, name='course_list'),

    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/module/<int:module_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

    # API endpoints
    path('api/courses/create/', views.create_course, name='create_course'),
    path('api/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('api/ai_assistant/', views.ai_assistant, name='ai_assistant'),
    # path('api/courses/', views.get_all_courses, name='get_all_courses'),
    # path('api/courses/<int:course_id>/', views.get_course_details, name='get_course_details'),
    # path('api/lessons/<int:lesson_id>/', views.get_lesson_details, name='get_lesson_details'),
    path('api/lessons/<int:lesson_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    # path('api/reviews/', views.get_review_items, name='get_review_items'),
]
