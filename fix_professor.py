# fix_professor.py
from main import app
from src.models.user import db, User
from src.models.academic import Professor, Discipline

with app.app_context():
    # 1. Localizar o usuário professor (username 77777777777)
    user = User.query.filter_by(username='77777777777').first()
    if not user:
        print("❌ Usuário não encontrado!")
        exit()

    print(f"✅ Usuário encontrado: ID={user.id}, Username={user.username}")

    # 2. Verificar se o perfil existe
    prof = Professor.query.filter_by(user_id=user.id).first()
    if not prof:
        print("⚠️ Perfil não encontrado. Criando...")
        prof = Professor(
            user_id=user.id,
            nome="Professor 777",
            cpf=user.username,
            departamento="Matemática"
        )
        db.session.add(prof)
        db.session.commit()
        print(f"✅ Perfil criado com ID={prof.id}")
    else:
        print(f"✅ Perfil já existe: ID={prof.id}, user_id={prof.user_id}")

    # 3. Atualizar a disciplina Matemática (ID 1) para usar este perfil
    disciplina = Discipline.query.get(1)
    if disciplina:
        print(f"📚 Disciplina '{disciplina.nome}' - professor_id atual: {disciplina.professor_id}")
        disciplina.professor_id = prof.id
        db.session.commit()
        print(f"✅ Disciplina atualizada: professor_id = {disciplina.professor_id}")
    else:
        print("❌ Disciplina Matemática (ID 1) não encontrada.")

    # 4. Verificar o resultado
    disciplinas_do_prof = Discipline.query.filter_by(professor_id=prof.id).all()
    if disciplinas_do_prof:
        print(f"🎉 Disciplinas do professor {prof.nome}: {[d.nome for d in disciplinas_do_prof]}")
    else:
        print("⚠️ Nenhuma disciplina atribuída ao professor.")

print("\n✅ Correção concluída. Reinicie o servidor e teste o login do professor.")