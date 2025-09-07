import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Course, Module, Lesson, Quiz, Question, Choice, UserProgress, UserQuizAttempt

# Simulated AI response for demo purposes
def get_ai_response(message, context=None):
    """Simulate an AI response. In production, this would call the Gemini API."""
    responses = [
        "That's a great question! Let me explain...",
        "I understand you're asking about this topic. Here's what you should know...",
        "Based on the current lesson, the answer is...",
        "Let me help clarify that concept for you...",
        "That's an interesting point. Consider this perspective..."
    ]
    return random.choice(responses)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_course(request):
    """
    Handles course creation from a user-provided topic and personalization.
    In a real scenario, this would call an LLM to generate the course structure.
    """
    try:
        data = json.loads(request.body)
        topic = data.get('topic')
        # Personalization data (role, age, education) is captured but not used in this simulation
        personalization = data.get('personalization', {})

        if not topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)

        # --- AI Prompt Simulation ---
        # In a real implementation, you would construct a detailed prompt for the LLM
        # and parse its JSON response. Here, we simulate that response.
        simulated_ai_json_response = {
            "course_title": f"Introduction to {topic}",
            "course_description": f"A comprehensive beginner's guide to {topic}.",
            "modules": [
                {
                    "title": f"Module 1: The Basics of {topic}",
                    "objective": f"Understand the fundamental concepts of {topic}.",
                    "lessons": [
                        {
                            "title": "Lesson 1.1: What is {topic}?",
                            "content": "This is the detailed content for the first lesson.",
                            "quiz_question": "What is the core idea of {topic}?",
                            "options": ["Incorrect A", "Incorrect B", "The core idea"],
                            "answer": "The core idea"
                        },
                        {
                            "title": "Lesson 1.2: Key Principles",
                            "content": "This lesson covers the key principles.",
                            "quiz_question": "What is a key principle?",
                            "options": ["Not this one", "This is the key principle", "Also not this one"],
                            "answer": "This is the key principle"
                        }
                    ]
                },
                {
                    "title": "Module 2: Advanced Concepts",
                    "objective": "Explore advanced concepts and applications.",
                    "lessons": [
                        {
                            "title": "Lesson 2.1: Advanced Topic A",
                            "content": "Content for advanced topic A.",
                            "quiz_question": "What is advanced topic A?",
                            "options": ["Advanced A", "Not A", "Not B"],
                            "answer": "Advanced A"
                        }
                    ]
                }
            ]
        }

        # --- Database Population ---
        with transaction.atomic():
            # Create the Course
            course = Course.objects.create(
                title=simulated_ai_json_response['course_title'],
                description=simulated_ai_json_response['course_description'],
                created_by=request.user
            )

            # Create Modules, Lessons, and Quizzes
            for module_order, module_data in enumerate(simulated_ai_json_response['modules']):
                module = Module.objects.create(
                    course=course,
                    title=module_data['title'],
                    description=module_data.get('objective', ''),
                    order=module_order
                )

                for lesson_order, lesson_data in enumerate(module_data['lessons']):
                    lesson = Lesson.objects.create(
                        module=module,
                        title=lesson_data['title'],
                        content=lesson_data['content'],
                        order=lesson_order
                    )

                    # Create the Quiz for the lesson
                    quiz = Quiz.objects.create(
                        lesson=lesson,
                        title=f"Quiz for {lesson.title}"
                    )
                    
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=lesson_data['quiz_question'],
                        order=0
                    )

                    # Add choices to the question
                    correct_answer = lesson_data['answer']
                    for choice_text in lesson_data['options']:
                        Choice.objects.create(
                            question=question,
                            choice_text=choice_text,
                            is_correct=(choice_text == correct_answer)
                        )

        return JsonResponse({'success': True, 'course_id': course.id})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    """Display a single lesson with its content."""
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        module_id=module_id,
        module__course_id=course_id
    )
    
    # Get or create user progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    # Get next and previous lessons for navigation
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
def ai_assistant(request):
    """Handle AI assistant chat messages."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            context = data.get('context', {})
            
            if not message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # Get AI response (in production, this would call the Gemini API)
            response = get_ai_response(message, context)
            
            return JsonResponse({
                'response': response,
                'context': context
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

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
