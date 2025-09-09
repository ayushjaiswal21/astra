import json
import random
import requests
from .tasks import generate_lesson_content
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Course, Module, Lesson, Quiz, Question, Choice, UserProgress, UserQuizAttempt

# --- Configuration ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:3.8b-mini-4k-instruct-q4_0"

def generate_with_ollama(prompt):
    print(f"Sending prompt to Ollama: {prompt}")
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, headers={"Content-Type": "application/json"}, timeout=120)
        response.raise_for_status()
        print(f"Received response from Ollama: {response.text}")
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        print(f"Error from Ollama: {e}")
        return f"Error from Ollama: {e}"

# New view to render the dedicated "Create Course" page
def create_course_page(request):
    return render(request, 'tutor/create_course.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_course(request):
    """
    Handles course creation, now including personalization data.
    """
    try:
        data = json.loads(request.body)
        topic = data.get('topic', 'Unnamed Topic')
        personalization = data.get('personalization', {})

        warning_message = None
        ai_response_json = None

        try:
            prompt = f'''
            You are an expert curriculum designer. Based on the following parameters, generate a comprehensive course outline in a structured JSON format.
            Topic: {topic}
            Target Audience Role: {personalization.get('role', 'Any')}
            Age Group: {personalization.get('age_group', 'Any')}
            Education Level: {personalization.get('education_level', 'Any')}

            The JSON output must include:
            - "course_title": A compelling title for the course.
            - "course_description": A brief, one-paragraph description of the course.
            - "modules": A list of 5-7 distinct modules, each with a "title" and "objective".
            - For each module, a list of lesson "titles".
            '''
            response_text = generate_with_ollama(prompt)
            cleaned_response = response_text.strip().replace('`', '').replace('json', '', 1)
            ai_response_json = json.loads(cleaned_response)

        except Exception as e:
            warning_message = f"API not working ({type(e).__name__}). A dummy course has been created."
            ai_response_json = {
                "course_title": f"Dummy Course: {topic}",
                "course_description": "This is a placeholder course because the AI service is unavailable.",
                "modules": [
                    {"title": "Module 1: Getting Started (Dummy)", "objective": "Sample objective.", "lessons": ["1.1: Dummy Lesson A", "1.2: Dummy Lesson B"]},
                    {"title": "Module 2: Advanced Topics (Dummy)", "objective": "Another sample objective.", "lessons": ["2.1: Placeholder A", "2.2: Placeholder B"]}
                ]
            }

        with transaction.atomic():
            course = Course.objects.create(
                title=ai_response_json['course_title'],
                description=ai_response_json['course_description']
            )
            lessons_to_generate = []
            for module_order, module_data in enumerate(ai_response_json['modules']):
                module = Module.objects.create(course=course, title=module_data['title'], description=module_data.get('objective', ''), order=module_order)
                for lesson_order, lesson_title in enumerate(module_data['lessons']):
                    lesson = Lesson.objects.create(module=module, title=lesson_title, content="", order=lesson_order)
                    lessons_to_generate.append(lesson.id)

        if not warning_message:
            for lesson_id in lessons_to_generate:
                generate_lesson_content.delay(lesson_id)

        return JsonResponse({'success': True, 'course_id': course.id, 'warning': warning_message})

    except Exception as e:
        return JsonResponse({'error': f'A critical error occurred: {str(e)}'}, status=500)


def course_list(request):
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'tutor/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'tutor/course_detail.html', {
        'course': course,
        'modules': course.modules.all().order_by('order'),
    })

def lesson_detail(request, course_id, module_id, lesson_id):
    lesson = get_object_or_404(
        Lesson, id=lesson_id, module_id=module_id, module__course_id=course_id
    )

    if not lesson.content:
        lesson.content = '''
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-md my-5">
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fas fa-robot h-5 w-5 text-blue-400"></i>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-blue-800">Content Generation in Progress</h3>
                    <div class="mt-2 text-sm text-blue-700">
                        <p>Our AI tutor is currently preparing this lesson for you. Please check back in a moment. You can refresh the page to see the update.</p>
                    </div>
                </div>
            </div>
        </div>
        '''

    progress, created = UserProgress.objects.get_or_create(
        session_key=request.session.session_key or 'anonymous',
        lesson=lesson
    )
    all_lessons = list(Lesson.objects.filter(module__course_id=course_id).order_by('module__order', 'order'))
    current_index = all_lessons.index(lesson)
    next_lesson = all_lessons[current_index + 1] if current_index + 1 < len(all_lessons) else None
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    
    return render(request, 'tutor/lesson_detail.html', {
        'course': lesson.module.course,
        'module': lesson.module,
        'lesson': lesson,
        'progress': progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'has_quiz': hasattr(lesson, 'quiz')
    })

def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().order_by('order')
    
    quiz_data = []
    for question in questions:
        choices = [
            {'id': choice.id, 'text': choice.choice_text}
            for choice in question.choices.all()
        ]
        random.shuffle(choices)
        quiz_data.append({
            'id': question.id,
            'text': question.question_text,
            'explanation': question.explanation,
            'choices': choices
        })
    
    return render(request, 'tutor/quiz_detail.html', {
        'quiz': quiz,
        'quiz_data': json.dumps(quiz_data),
        'lesson': quiz.lesson
    })

@require_http_methods(["POST"])
def submit_quiz(request, quiz_id):
    try:
        data = json.loads(request.body)
        quiz = Quiz.objects.get(id=quiz_id)
        answers = data.get('answers', {})
        
        total_questions = quiz.questions.count()
        correct_answers = 0
        
        for question_id, choice_id in answers.items():
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                correct_choice = question.choices.get(is_correct=True)
                if str(correct_choice.id) == choice_id:
                    correct_answers += 1
            except (Question.DoesNotExist, Choice.DoesNotExist):
                pass
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        UserQuizAttempt.objects.create(
            session_key=request.session.session_key or 'anonymous',
            quiz=quiz,
            score=score
        )
        
        if score >= 70:
            UserProgress.objects.update_or_create(
                session_key=request.session.session_key or 'anonymous',
                lesson=quiz.lesson,
                defaults={'completed': True}
            )
        
        return JsonResponse({
            'success': True,
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'passed': score >= 70
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_http_methods(["POST"])
def ai_assistant(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        lesson_id = data.get('context', {}).get('lesson_id')

        if not message or not lesson_id:
            return JsonResponse({'error': 'Message and lesson_id are required'}, status=400)

        lesson = get_object_or_404(Lesson, id=lesson_id)

        context_text = lesson.content

        prompt = f'''
        Context: You are an AI tutor explaining a lesson. The lesson content is as follows:
        ---
        {context_text}
        ---
        Based ONLY on the context above, answer the user's question.
        User Question: {message}
        '''
        
        response_text = generate_with_ollama(prompt)

        return JsonResponse({
            'response': response_text,
            'context': data.get('context', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def delete_course(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        return JsonResponse({'success': True, 'message': 'Course deleted successfully.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress, created = UserProgress.objects.get_or_create(
        session_key=request.session.session_key or 'anonymous',
        lesson=lesson
    )
    progress.completed = True
    progress.save()
    return redirect('tutor:lesson_detail', course_id=lesson.module.course.id, module_id=lesson.module.id, lesson_id=lesson.id)
