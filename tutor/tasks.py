import json
import google.generativeai as genai
from celery import shared_task
from django.conf import settings
from django.db import transaction
from .models import Lesson, Quiz, Question, Choice

# It's good practice to configure the client within the task
# to ensure it's initialized in the worker process.
genai.configure(api_key=settings.GEMINI_API_KEY)

@shared_task
def generate_lesson_content(lesson_id):
    """
    Background task to generate content and a quiz for a single lesson.
    """
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        if lesson.content:
            return f"Lesson {lesson_id} already has content."

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        You are an expert educator. Generate the content for a lesson titled \"{lesson.title}\" within the module \"{lesson.module.title}\".
        The module's objective is: {lesson.module.description}
        
        The output must be a JSON object with the following structure:
        - \"lesson_content\": The full lesson content in Markdown format. It should be detailed, clear, and easy to understand.
        - \"quiz_question\": A multiple-choice question to test the core concept of the lesson.
        - \"options\": A list of 4 strings representing the choices for the multiple-choice question.
        - \"answer\": The correct choice from the options list.
        """
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('`', '').replace('json', '', 1)
        ai_response_json = json.loads(cleaned_response)

        with transaction.atomic():
            lesson.content = ai_response_json['lesson_content']
            lesson.save()

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
        return f"Successfully generated content for lesson {lesson_id}."

    except Lesson.DoesNotExist:
        return f"Error: Lesson with ID {lesson_id} not found."
    except Exception as e:
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.content = f"### Error Generating Content\n\nWe encountered an issue while preparing this lesson: `{str(e)}`\n\nPlease try refreshing later or contact support."
        lesson.save()
        return f"Failed to generate content for lesson {lesson_id}: {str(e)}"