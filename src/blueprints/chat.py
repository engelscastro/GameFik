"""
Blueprint para sistema de chat por disciplina
Responsável por gerenciar chats, mensagens, anúncios,
pin de mensagens e criação automática de chats.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session

from src.models.academic import Discipline, Student, Enrollment, DisciplineChat, ChatMessage
from src.models.user import db, User
from .utils import login_required, teacher_required, teacher_or_admin_required

# Criar blueprint
chat_bp = Blueprint('chat', __name__)


# ========== CHAT DA DISCIPLINA ==========

@chat_bp.route('/disciplines/<int:discipline_id>/chat', methods=['GET'])
@login_required
def get_discipline_chat(discipline_id):
    """Obter mensagens do chat de uma disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        discipline = Discipline.query.get_or_404(discipline_id)

        # Verificar acesso à disciplina
        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            if not student:
                return jsonify({
                    'success': False,
                    'error': 'Perfil de estudante não encontrado'
                }), 403

            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                discipline_id=discipline_id,
                status='active'
            ).first()

            if not enrollment:
                return jsonify({
                    'success': False,
                    'error': 'Você não está matriculado nesta disciplina'
                }), 403

        # Garantir que o chat existe
        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            # Criar chat automaticamente se não existir
            chat = DisciplineChat(discipline_id=discipline_id, is_active=True)
            db.session.add(chat)
            db.session.commit()
            print(f"🔄 Chat criado automaticamente para disciplina {discipline.nome}")

        # Buscar mensagens (mais recentes primeiro)
        messages = ChatMessage.query.filter_by(chat_id=chat.id).order_by(
            ChatMessage.created_at.desc()
        ).limit(100).all()

        # Reverter para ordem cronológica
        messages.reverse()

        return jsonify({
            'success': True,
            'chat': {
                'id': chat.id,
                'discipline_id': chat.discipline_id,
                'discipline_name': discipline.nome,
                'is_active': chat.is_active
            },
            'messages': [message.to_dict() for message in messages],
            'user_role': current_user.role,
            'total_messages': len(messages)
        })

    except Exception as e:
        print(f"❌ Erro ao carregar chat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/disciplines/<int:discipline_id>/chat/messages', methods=['POST'])
@login_required
def send_chat_message(discipline_id):
    """Enviar mensagem no chat da disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        data = request.json

        if not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Conteúdo da mensagem é obrigatório'
            }), 400

        discipline = Discipline.query.get_or_404(discipline_id)

        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            if not student:
                return jsonify({
                    'success': False,
                    'error': 'Perfil de estudante não encontrado'
                }), 403

            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                discipline_id=discipline_id,
                status='active'
            ).first()

            if not enrollment:
                return jsonify({
                    'success': False,
                    'error': 'Você não está matriculado nesta disciplina'
                }), 403

        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            chat = DisciplineChat(discipline_id=discipline_id)
            db.session.add(chat)
            db.session.commit()

        message = ChatMessage(
            chat_id=chat.id,
            user_id=current_user.id,
            message_type=data.get('message_type', 'text'),
            content=data['content'],
            file_url=data.get('file_url')
        )

        db.session.add(message)
        db.session.commit()

        if current_user.role == 'student':
            current_user.add_xp(2)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Mensagem enviada com sucesso! +2 XP',
            'chat_message': message.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/chat/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_chat_message(message_id):
    """Deletar mensagem do chat (apenas própria mensagem ou professor)"""
    try:
        current_user = User.query.get(session['user_id'])
        message = ChatMessage.query.get_or_404(message_id)

        can_delete = (
                message.user_id == current_user.id or
                current_user.role in ['teacher', 'admin'] or
                (current_user.role == 'teacher' and
                 message.chat.discipline.professor_id == current_user.id)
        )

        if not can_delete:
            return jsonify({
                'success': False,
                'error': 'Sem permissão para deletar esta mensagem'
            }), 403

        db.session.delete(message)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Mensagem deletada com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== FUNCIONALIDADES DO PROFESSOR ==========

@chat_bp.route('/chat/messages/<int:message_id>/pin', methods=['PUT'])
@teacher_required
def pin_chat_message(message_id):
    """Fixar/Desafixar mensagem (apenas professores)"""
    try:
        message = ChatMessage.query.get_or_404(message_id)
        message.is_pinned = not message.is_pinned
        db.session.commit()

        action = "fixada" if message.is_pinned else "desafixada"
        return jsonify({
            'success': True,
            'message': f'Mensagem {action} com sucesso',
            'chat_message': message.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/disciplines/<int:discipline_id>/chat/announcement', methods=['POST'])
@teacher_required
def send_announcement(discipline_id):
    """Enviar anúncio (apenas professores)"""
    try:
        current_user = User.query.get(session['user_id'])
        data = request.json

        if not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Conteúdo do anúncio é obrigatório'
            }), 400

        discipline = Discipline.query.get_or_404(discipline_id)

        from src.models.academic import Professor
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Você não é o professor desta disciplina'
            }), 403

        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            chat = DisciplineChat(discipline_id=discipline_id)
            db.session.add(chat)
            db.session.commit()

        announcement = ChatMessage(
            chat_id=chat.id,
            user_id=current_user.id,
            message_type='announcement',
            content=data['content'],
            is_pinned=True
        )

        db.session.add(announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Anúncio enviado com sucesso',
            'chat_message': announcement.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== GARANTIR CRIAÇÃO DE CHAT ==========

@chat_bp.route('/disciplines/<int:discipline_id>/chat/ensure', methods=['POST'])
@login_required
def ensure_discipline_chat(discipline_id):
    """Garante que um chat existe para a disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        print(f"🔍 DEBUG - Usuário: {current_user.username} (role: {current_user.role})")

        discipline = Discipline.query.get_or_404(discipline_id)
        print(f"🔍 DEBUG - Disciplina: {discipline.nome}")

        # VERIFICAÇÃO PARA ESTUDANTES
        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            print(f"🔍 DEBUG - Perfil estudante encontrado: {student is not None}")

            if not student:
                print(f"❌ Perfil de estudante não encontrado para user_id {current_user.id}")
                return jsonify({
                    'success': False,
                    'error': 'Perfil de estudante não encontrado'
                }), 403

            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                discipline_id=discipline_id,
                status='active'
            ).first()
            print(f"🔍 DEBUG - Matrícula encontrada: {enrollment is not None}")

            if not enrollment:
                print(f"❌ Estudante {student.nome} NÃO está matriculado em {discipline.nome}")
                return jsonify({
                    'success': False,
                    'error': f'Você não está matriculado na disciplina {discipline.nome}'
                }), 403
            else:
                print(f"✅ Estudante {student.nome} está matriculado!")

        # Verificar se chat já existe
        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            chat = DisciplineChat(discipline_id=discipline_id, is_active=True)
            db.session.add(chat)
            db.session.commit()
            print(f"✅ Chat criado para disciplina: {discipline.nome}")

        return jsonify({'success': True, 'chat_id': chat.id, 'message': 'Chat disponível'})

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/admin/create-all-chats', methods=['POST'])
@teacher_or_admin_required
def create_all_chats():
    """Cria chats para todas as disciplinas que não têm"""
    try:
        disciplines_without_chat = Discipline.query.filter(
            ~Discipline.chat.any()
        ).all()

        created_count = 0
        for discipline in disciplines_without_chat:
            chat = DisciplineChat(discipline_id=discipline.id, is_active=True)
            db.session.add(chat)
            created_count += 1
            print(f"✅ Chat criado para: {discipline.nome}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Chats criados para {created_count} disciplinas',
            'created_count': created_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ROTAS DE DEBUG ==========

@chat_bp.route('/debug/chats-status', methods=['GET'])
@teacher_or_admin_required
def debug_chats_status():
    """Debug do status dos chats"""
    try:
        disciplines = Discipline.query.all()
        result = []

        for discipline in disciplines:
            chat = DisciplineChat.query.filter_by(discipline_id=discipline.id).first()

            # Contar mensagens no chat
            message_count = 0
            if chat:
                message_count = ChatMessage.query.filter_by(chat_id=chat.id).count()

            result.append({
                'disciplina_id': discipline.id,
                'disciplina_nome': discipline.nome,
                'tem_chat': bool(chat),
                'chat_id': chat.id if chat else None,
                'mensagens': message_count,
                'ano_turma': discipline.ano_turma,
                'nivel_ensino': discipline.nivel_ensino
            })

        # Estatísticas
        total_disciplinas = len(result)
        disciplinas_com_chat = len([d for d in result if d['tem_chat']])
        disciplinas_sem_chat = total_disciplinas - disciplinas_com_chat

        return jsonify({
            'success': True,
            'estatisticas': {
                'total_disciplinas': total_disciplinas,
                'disciplinas_com_chat': disciplinas_com_chat,
                'disciplinas_sem_chat': disciplinas_sem_chat,
                'percentual_com_chat': f"{(disciplinas_com_chat/total_disciplinas)*100:.1f}%" if total_disciplinas > 0 else "0%"
            },
            'disciplinas': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== UPLOAD DE IMAGEM ==========
@chat_bp.route('/disciplines/<int:discipline_id>/chat/upload', methods=['POST'])
@login_required
def upload_chat_image(discipline_id):
    """Enviar imagem no chat (retorna URL para inclusão na mensagem)"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhuma imagem enviada'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Arquivo vazio'}), 400

        # Validar extensão
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
            return jsonify({'success': False, 'error': 'Formato não suportado. Use PNG, JPG, GIF ou WEBP.'}), 400

        # Gerar nome único
        import uuid
        import os
        from flask import current_app

        # Criar pasta de uploads se não existir
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"chat_{discipline_id}_{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(upload_dir, filename))

        # URL pública da imagem
        image_url = f"/static/uploads/{filename}"
        return jsonify({'success': True, 'url': image_url})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ========== ÚLTIMA MENSAGEM (para notificações) ==========
@chat_bp.route('/disciplines/<int:discipline_id>/chat/latest', methods=['GET'])
@login_required
def get_latest_message(discipline_id):
    """Retorna a última mensagem do chat (para verificar novas mensagens)"""
    try:
        chat = DisciplineChat.query.filter_by(discipline_id=discipline_id).first()
        if not chat:
            return jsonify({
                'success': True,
                'last_message_id': None,
                'last_message_preview': None
            })
        last_message = ChatMessage.query.filter_by(chat_id=chat.id).order_by(
            ChatMessage.created_at.desc()
        ).first()
        return jsonify({
            'success': True,
            'last_message_id': last_message.id if last_message else None,
            'last_message_preview': last_message.content[:50] if last_message else None,
            'last_message_time': last_message.created_at.isoformat() if last_message else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== INDICADOR "DIGITANDO" ==========
# Dicionário simples para armazenar status de digitação
typing_status = {}  # chave: f"{discipline_id}:{user_id}", valor: timestamp

@chat_bp.route('/disciplines/<int:discipline_id>/chat/typing', methods=['POST'])
@login_required
def set_typing_status(discipline_id):
    """Define que o usuário está digitando"""
    try:
        user_id = session['user_id']
        key = f"{discipline_id}:{user_id}"
        typing_status[key] = datetime.utcnow().timestamp()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chat_bp.route('/disciplines/<int:discipline_id>/chat/typing-status', methods=['GET'])
@login_required
def get_typing_status(discipline_id):
    """Retorna lista de usuários que estão digitando na disciplina"""
    try:
        current_user_id = session['user_id']
        now = datetime.utcnow().timestamp()
        timeout = 3  # segundos
        typing_users = []
        keys_to_remove = []
        for key, ts in typing_status.items():
            disc, uid = key.split(':')
            if int(disc) == discipline_id and uid != str(current_user_id):
                if now - ts < timeout:
                    user = User.query.get(int(uid))
                    if user:
                        typing_users.append({
                            'user_id': user.id,
                            'username': user.username
                        })
                else:
                    keys_to_remove.append(key)
        for key in keys_to_remove:
            del typing_status[key]
        return jsonify({'success': True, 'typing_users': typing_users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== REAÇÕES ==========
@chat_bp.route('/chat/messages/<int:message_id>/react', methods=['POST'])
@login_required
def react_to_message(message_id):
    """Adiciona ou remove uma reação (emoji) a uma mensagem"""
    try:
        data = request.json
        reaction = data.get('reaction')
        allowed = ['👍', '❤️', '😂', '😮', '😢', '🙏']
        if reaction not in allowed:
            return jsonify({'success': False, 'error': 'Reação inválida'}), 400

        message = ChatMessage.query.get_or_404(message_id)
        user_id = session['user_id']

        # Se o modelo ChatMessage não tiver um campo 'reactions', podemos usar um dicionário auxiliar
        # (armazenamento simples em memória - para produção use um campo JSON no banco)
        if not hasattr(message, 'reactions_cache'):
            message.reactions_cache = {}  # { "👍": [user_id1, user_id2], ... }

        # Atualizar reações
        if reaction in message.reactions_cache:
            if user_id in message.reactions_cache[reaction]:
                message.reactions_cache[reaction].remove(user_id)
                if not message.reactions_cache[reaction]:
                    del message.reactions_cache[reaction]
            else:
                message.reactions_cache[reaction].append(user_id)
        else:
            message.reactions_cache[reaction] = [user_id]

        # Para persistir, seria ideal adicionar uma coluna JSON no banco.
        # Como é um exemplo, vamos apenas retornar o estado atual.
        return jsonify({
            'success': True,
            'reactions': message.reactions_cache
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500