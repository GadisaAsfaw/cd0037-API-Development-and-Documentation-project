from crypt import methods
from nis import cat
import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def format_category(selection):
    categories = {}
    for category in selection:
        categories[category.id] = category.type
    return categories


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route('/categories')
    def get_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = format_category(selection)
        return jsonify({
            'success': True,
            'categories': categories,
        })

    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        cat_selection = Category.query.order_by(Category.id).all()
        categories = format_category(cat_selection)

        if len(current_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': categories,
            'current_category': 'History'
        })

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter(Question.id == id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            return jsonify({
                'success': True
            })
        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def search_or_create_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)
        question = body.get('question', None)
        answer = body.get('answer', None)
        category = body.get('category', None)
        difficulty = body.get('difficulty', None)

        if search:
            selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': 'History'
            })
        else:
            try:
                question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
                question.insert()
                return jsonify({'success': True})
            except Exception:
                abort(422)

    @app.route('/categories/<int:cat_id>/questions')
    def get_questions_for_category(cat_id):
        selection = Question.query.filter(Question.category == cat_id).all()
        current_category = Category.query.filter(Category.id == cat_id).one_or_none()
        current_questions = paginate_questions(request, selection)
        if len(current_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': current_category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def get_next_question():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)

        try:
            if quiz_category['id'] != 0:
                questions = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            question = questions[random.randint(0, len(questions)-1)]
            return jsonify({
                'success': True,
                'question': question.format()
            })
        except Exception as e:
            print(e)
            abort(404)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    return app
