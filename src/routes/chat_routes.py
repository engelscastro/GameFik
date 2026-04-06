# src/routes/chat_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import DisciplineChat, ChatMessage, Discipline, Student, Enrollment
from functools import wraps

chat_bp = Blueprint('chat', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

@chat_bp.route('/disciplines/<int:discipline_id>/chat', methods=['GET'])
@login_required
def get_chat_messages(discipline_id):
    try:
        # Verificar acesso
        user = User.query.get(session['user_id'])
        discipline = Discipline.query.get(discipline_id)

        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        # Buscar ou criar chat
        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            chat = DisciplineChat(discipline_id=discipline_id)
            db.session.add(chat)
            db.session.commit()

        messages = ChatMessage.query.filter_by(chat_id=chat.id).order_by(ChatMessage.created_at).all()

        return jsonify({
            'success': True,
            'messages': [m.to_dict() for m in messages],
            'discipline': discipline.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/disciplines/<int:discipline_id>/chat/messages', methods=['POST'])
@login_required
def send_message(discipline_id):
    try:
        data = request.json
        if not data.get('content'):
            return jsonify({'success': False, 'error': 'Mensagem vazia'}), 400

        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            chat = DisciplineChat(discipline_id=discipline_id)
            db.session.add(chat)
            db.session.commit()

        message = ChatMessage(
            chat_id=chat.id,
            user_id=session['user_id'],
            content=data['content'],
            message_type=data.get('message_type', 'text')
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({'success': True, 'message': message.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500