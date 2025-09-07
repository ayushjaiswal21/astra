import json
import random
import google.generativeai as genai
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Course, Module, Lesson, Quiz, Question, Choice, UserProgress, UserQuizAttempt

# Configure the Gemini API client
genai.configure(api_key=settings.GEMINI_API_KEY)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_course(request):
    """
    Handles course creation. Calls the Gemini API to generate the course structure,
    but not the content itself, which will be generated on-demand.
    """
    try:
        data = json.loads(request.body)
        topic = data.get('topic')
        if not topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)

        # 1. --- AI Call to Generate Course Structure ---
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = f"""
        You are an expert curriculum designer. Generate a comprehensive course outline for the topic "{topic}".
        The output must be a JSON object with the following structure:
        - "course_title": A compelling title for the course.
        - "course_description": A brief, one-paragraph description of the course.
        - "modules": A list of 5-7 module objects. Each module object must have:
          - "title": The title of the module.
          - "objective": A one-sentence objective for the module.
          - "lessons": A list of lesson titles (strings).

        Example:
        {{
          "course_title": "Introduction to Python Programming",
          "course_description": "This course offers a comprehensive introduction to the Python programming language, covering fundamental concepts and practical applications.",
          "modules": [
            {{
              "title": "Module 1: Python Basics",
              "objective": "Understand the fundamental syntax and data types in Python.",
              "lessons": ["1.1: What is Python?", "1.2: Variables and Data Types", "1.3: Your First Python Program"]
            }}
          ]
        }}
        """
        response = model.generate_content(prompt)
        
        # Clean up the response and load it as JSON
        cleaned_response = response.text.strip().replace('`', '').replace('json', '', 1)
        ai_response_json = json.loads(cleaned_response)

        # 2. --- Database Population ---
        with transaction.atomic():
            course = Course.objects.create(
                title=ai_response_json['course_title'],
                description=ai_response_json['course_description'],
                created_by=request.user
            )

            for module_order, module_data in enumerate(ai_response_json['modules']):
                module = Module.objects.create(
                    course=course,
                    title=module_data['title'],
                    description=module_data.get('objective', ''),
                    order=module_order
                )
                for lesson_order, lesson_title in enumerate(module_data['lessons']):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_title,
                        content="",  # Content will be generated on-demand
                        order=lesson_order
                    )

        return JsonResponse({'success': True, 'course_id': course.id})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Failed to decode AI response. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)


@login_required
def course_list(request):
    """Display all available courses."""
    courses = Course.objects.all()
    return render(request, 'tutor/course_list.html', {'courses': courses})

@login_required
def course_detail(request, course_id):
    """Display course details and modules."""
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'tutor/course_detail.html', {
        'course': course,
        'modules': course.modules.all().order_by('order'),
    })

@login_required
def lesson_detail(request, course_id, module_id, lesson_id):
    """
    Display a single lesson. If the lesson content is empty, generate it using the AI.
    """
    lesson = get_object_or_404(
        Lesson, id=lesson_id, module_id=module_id, module__course_id=course_id
    )

    # --- On-Demand Content Generation ---
    if not lesson.content:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            prompt = f"""
You are an expert educator. Generate the content for a lesson titled \"{lesson.title}\" within the module \"{lesson.module.title}\".
            The module's objective is: {lesson.module.description}
            
            The output must be a JSON object with the following structure:
            - \"lesson_content\": The full lesson content in Markdown format. It should be detailed, clear, and easy to understand.
            - \"quiz_question\": A multiple-choice question to test the core concept of the lesson.
            - \"options\": A list of 4 strings representing the choices for the multiple-choice question.
            - \"answer\": The correct choice from the options list.

            Example:
            {{
              \"lesson_content\": \"Variables are fundamental to programming...\",
              \"quiz_question\": \"What is a variable in Python?\",
              \"options\": [\"A constant value\", \"A container for storing data\", \"A type of function\", \"A reserved keyword\"],
              \"answer\": \"A container for storing data\"
            }}
            """
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().replace('`', '').replace('json', '', 1)
            ai_response_json = json.loads(cleaned_response)

            with transaction.atomic():
                # Update lesson with generated content
                lesson.content = ai_response_json['lesson_content']
                lesson.save()

                # Create the quiz for the lesson
                quiz = Quiz.objects.create(lesson=lesson, title=f"Quiz for {lesson.title}")
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=ai_response_json['quiz_question'],
                    order=0
                )
                for choice_text in ai_response_json['options']:
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=(choice_text == ai_response_json['answer'])
                    )
        except Exception as e:
            # In case of AI failure, show a message instead of crashing
            lesson.content = f"Failed to generate lesson content. Error: {str(e)}"

    # --- Standard View Logic ---
    progress, created = UserProgress.objects.get_or_create(user=request.user, lesson=lesson)
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


@login_required
def quiz_detail(request, quiz_id):
    """Display a quiz with its questions and choices."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().order_by('order')
    
    # Prepare question data with choices
    quiz_data = []
    for question in questions:
        choices = [
            {'id': choice.id, 'text': choice.choice_text}
            for choice in question.choices.all()
        ]
        random.shuffle(choices)  # Shuffle choices for each question
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

@login_required
@require_http_methods(["POST"])
def submit_quiz(request, quiz_id):
    """Handle quiz submission and calculate score."""
    try:
        data = json.loads(request.body)
        quiz = Quiz.objects.get(id=quiz_id)
        answers = data.get('answers', {})
        
        # Calculate score
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
        
        # Save quiz attempt
        UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score
        )
        
        # Update lesson progress if score is passing (e.g., >= 70%)
        if score >= 70:
            UserProgress.objects.update_or_create(
                user=request.user,
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

@login_required
@require_http_methods(["POST"])
def ai_assistant(request):
    """Handle AI assistant chat messages using the Gemini API."""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        lesson_id = data.get('context', {}).get('lesson_id')

        if not message or not lesson_id:
            return JsonResponse({'error': 'Message and lesson_id are required'}, status=400)

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # For optimization, we could summarize the content first or use embeddings.
        # For now, we use the full content to ensure the highest quality answers.
        context_text = lesson.content

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        Context: You are an AI tutor explaining a lesson. The lesson content is as follows:
        ---
        {context_text}
        ---
        Based ONLY on the context above, answer the user's question.
        User Question: {message}
        """
        
        response = model.generate_content(prompt)

        return JsonResponse({
            'response': response.text,
            'context': data.get('context', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_course(request, course_id):
    """Deletes a course after verifying the user is the owner."""
    try:
        course = get_object_or_404(Course, id=course_id)
        # Security check: only the user who created the course can delete it.
        if course.created_by != request.user:
            return JsonResponse({'error': 'You are not authorized to delete this course.'}, status=403)
        
        course.delete()
        return JsonResponse({'success': True, 'message': 'Course deleted successfully.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.completed = True
    progress.save()
    return redirect('tutor:lesson_detail', course_id=lesson.module.course.id, module_id=lesson.module.id, lesson_id=lesson.id)
