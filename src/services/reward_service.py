# src/services/reward_service.py
"""
Service Layer para Recompensas - Lógica de Negócio
Responsável por toda a lógica de sistema de recompensas.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - get_all_rewards(): Listar todas as recompensas
  - create_reward(): Criar nova recompensa (admin)
  - update_reward(): Atualizar recompensa (admin)
  - delete_reward(): Deletar recompensa (admin)
  - get_user_rewards(): Obter recompensas do usuário
  - get_user_pending_rewards(): Recompensas pendentes de entrega
  - purchase_reward(): Comprar recompensa com coins
  - redeem_reward(): Marcar recompensa como entregue
  - check_rewards(): Verificar novas recompensas disponíveis
  - get_reward_summary(): Resumo do sistema de recompensas (admin)
"""

from datetime import datetime
from src.models.user import User, Reward, UserReward, db


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class RewardNotFound(Exception):
    """Exceção quando recompensa não é encontrada"""
    pass


class InsufficientCoins(Exception):
    """Exceção quando usuário não tem coins suficientes"""
    pass


class RewardAlreadyRedeemed(Exception):
    """Exceção quando recompensa já foi resgatada"""
    pass


class InvalidRewardData(Exception):
    """Exceção quando dados são inválidos"""
    pass


class UserNotFound(Exception):
    """Exceção quando usuário não é encontrado"""
    pass


# ============================================================================
# REWARD SERVICE
# ============================================================================

class RewardService:
    """Service para gerenciar recompensas e resgate de pontos"""

    # ========================================================================
    # LEITURA - Recompensas
    # ========================================================================

    @staticmethod
    def get_all_rewards():
        """Obter todas as recompensas disponíveis (ativas)"""
        try:
            rewards = Reward.query.filter_by(is_active=True).all()
            return [reward.to_dict() for reward in rewards if reward is not None]
        except Exception as e:
            raise Exception(f"Erro ao buscar recompensas: {str(e)}")

    @staticmethod
    def get_all_rewards_admin():
        """Obter TODAS as recompensas (admin) - incluindo inativas"""
        try:
            rewards = Reward.query.all()
            return [reward.to_dict() for reward in rewards if reward is not None]
        except Exception as e:
            raise Exception(f"Erro ao buscar recompensas (admin): {str(e)}")

    @staticmethod
    def get_reward_details(reward_id):
        """Obter detalhes de uma recompensa"""
        try:
            reward = Reward.query.get(reward_id)
            if not reward:
                raise RewardNotFound(f"Recompensa {reward_id} não encontrada")
            return reward.to_dict()
        except RewardNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar detalhes da recompensa: {str(e)}")

    @staticmethod
    def get_user_rewards(user_id):
        """Obter TODAS as recompensas do usuário"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            user_rewards = UserReward.query.filter_by(user_id=user_id).all()
            return [ur.to_dict() for ur in user_rewards if ur is not None]
        except UserNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar recompensas do usuário: {str(e)}")

    @staticmethod
    def get_user_pending_rewards(user_id):
        """Obter recompensas PENDENTES (não resgatadas)"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            pending_rewards = UserReward.query.filter_by(
                user_id=user_id,
                is_redeemed=False
            ).all()
            return [ur.to_dict() for ur in pending_rewards if ur is not None]
        except UserNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar recompensas pendentes: {str(e)}")

    @staticmethod
    def get_user_redeemed_rewards(user_id):
        """Obter recompensas JÁ RESGATADAS"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            redeemed_rewards = UserReward.query.filter_by(
                user_id=user_id,
                is_redeemed=True
            ).all()
            return [ur.to_dict() for ur in redeemed_rewards if ur is not None]
        except UserNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar recompensas resgatadas: {str(e)}")

    # ========================================================================
    # CRIACAO/ATUALIZACAO/DELECAO - Recompensas (Admin)
    # ========================================================================

    @staticmethod
    def create_reward(data):
        """
        Criar nova recompensa (admin)

        Args:
            data: Dict com:
                - name (obrigatório)
                - description
                - icon (emoji, padrão '🎁')
                - coin_cost (obrigatório)
                - image_url (opcional)

        Returns:
            dict: Recompensa criada
        """
        try:
            if not data.get('name'):
                raise InvalidRewardData('Nome da recompensa é obrigatório')

            if data.get('coin_cost') is None:
                raise InvalidRewardData('Custo em coins é obrigatório')

            if int(data.get('coin_cost')) < 0:
                raise InvalidRewardData('Custo em coins não pode ser negativo')

            reward = Reward(
                name=data.get('name'),
                description=data.get('description', ''),
                icon=data.get('icon', '🎁'),
                coin_cost=int(data.get('coin_cost')),
                image_url=data.get('image_url'),
                is_active=True
            )

            db.session.add(reward)
            db.session.commit()

            return reward.to_dict()
        except InvalidRewardData:
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao criar recompensa: {str(e)}")

    @staticmethod
    def update_reward(reward_id, data):
        """
        Atualizar recompensa (admin)

        Args:
            reward_id: ID da recompensa
            data: Dict com campos a atualizar

        Returns:
            dict: Recompensa atualizada
        """
        try:
            reward = Reward.query.get(reward_id)
            if not reward:
                raise RewardNotFound(f"Recompensa {reward_id} não encontrada")

            if 'name' in data:
                reward.name = data['name']
            if 'description' in data:
                reward.description = data['description']
            if 'icon' in data:
                reward.icon = data['icon']
            if 'coin_cost' in data:
                if int(data['coin_cost']) < 0:
                    raise InvalidRewardData('Custo em coins não pode ser negativo')
                reward.coin_cost = int(data['coin_cost'])
            if 'image_url' in data:
                reward.image_url = data['image_url']
            if 'is_active' in data:
                reward.is_active = data['is_active']

            db.session.commit()

            return reward.to_dict()
        except (RewardNotFound, InvalidRewardData):
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao atualizar recompensa: {str(e)}")

    @staticmethod
    def delete_reward(reward_id):
        """
        Deletar recompensa (admin)
        Só permite deletar se nenhum usuário comprou

        Args:
            reward_id: ID da recompensa

        Returns:
            dict: Status da deleção
        """
        try:
            reward = Reward.query.get(reward_id)
            if not reward:
                raise RewardNotFound(f"Recompensa {reward_id} não encontrada")

            # Verificar se há usuários com essa recompensa
            user_count = UserReward.query.filter_by(reward_id=reward_id).count()

            if user_count > 0:
                raise ValueError(
                    f'Não é possível deletar recompensa com {user_count} usuário(s) que já compraram'
                )

            db.session.delete(reward)
            db.session.commit()

            return {'success': True, 'message': 'Recompensa deletada com sucesso'}
        except (RewardNotFound, ValueError):
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao deletar recompensa: {str(e)}")

    # ========================================================================
    # COMPRA E RESGATE - Recompensas (Usuários)
    # ========================================================================

    @staticmethod
    def purchase_reward(user_id, reward_id):
        """
        COMPRAR recompensa com coins

        Args:
            user_id: ID do usuário
            reward_id: ID da recompensa

        Returns:
            dict: Status da compra com dados da transação

        Raises:
            UserNotFound: Se usuário não existe
            RewardNotFound: Se recompensa não existe
            InsufficientCoins: Se não tem coins suficientes
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            reward = Reward.query.get(reward_id)
            if not reward:
                raise RewardNotFound(f"Recompensa {reward_id} não encontrada")

            if not reward.is_active:
                raise ValueError("Recompensa não está mais disponível")

            # Validar coins
            if user.coins < reward.coin_cost:
                raise InsufficientCoins(
                    f'Coins insuficientes. Você tem {user.coins}, '
                    f'mas precisa de {reward.coin_cost}'
                )

            # Descontar coins
            user.coins -= reward.coin_cost

            # Criar registro de recompensa do usuário
            user_reward = UserReward(
                user_id=user_id,
                reward_id=reward_id,
                purchase_date=datetime.utcnow(),
                is_redeemed=False
            )

            db.session.add(user_reward)
            db.session.commit()

            return {
                'success': True,
                'message': f'Recompensa "{reward.name}" comprada com sucesso!',
                'reward': reward.to_dict(),
                'remaining_coins': user.coins,
                'user_reward_id': user_reward.id,
                'purchase_date': user_reward.purchase_date.isoformat()
            }
        except (UserNotFound, RewardNotFound, InsufficientCoins, ValueError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao comprar recompensa: {str(e)}")

    @staticmethod
    def redeem_reward(user_reward_id, user_id):
        """
        MARCAR recompensa como resgatada/entregue

        Args:
            user_reward_id: ID da recompensa do usuário
            user_id: ID do usuário (para validação)

        Returns:
            dict: Status do resgate
        """
        try:
            user_reward = UserReward.query.filter_by(
                id=user_reward_id,
                user_id=user_id
            ).first()

            if not user_reward:
                raise RewardNotFound('Recompensa do usuário não encontrada')

            if user_reward.is_redeemed:
                raise RewardAlreadyRedeemed('Recompensa já foi resgatada')

            user_reward.is_redeemed = True

            db.session.commit()

            reward = Reward.query.get(user_reward.reward_id)
            reward_name = reward.name if reward else 'Recompensa'

            return {
                'success': True,
                'message': f'Recompensa "{reward_name}" resgatada com sucesso!',
                'user_reward': user_reward.to_dict(),
                'redeemed_date': datetime.utcnow().isoformat()
            }
        except (RewardNotFound, RewardAlreadyRedeemed):
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao resgatar recompensa: {str(e)}")

    # ========================================================================
    # VERIFICACAO - Recompensas
    # ========================================================================

    @staticmethod
    def check_rewards(user_id):
        """
        VERIFICAR se novas recompensas se tornaram disponíveis
        Função chamada quando usuário ganha coins

        Returns:
            list: Novas recompensas disponíveis (que o usuário pode comprar)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            new_available = []
            all_rewards = Reward.query.filter_by(is_active=True).all()

            # IDs das recompensas que o usuário já comprou
            purchased_ids = set(
                ur.reward_id for ur in UserReward.query.filter_by(user_id=user_id).all()
            )

            for reward in all_rewards:
                if reward is None:
                    continue

                # Verificar se usuário já comprou
                if reward.id in purchased_ids:
                    continue

                # Verificar se tem coins suficientes
                if user.coins >= reward.coin_cost:
                    new_available.append(reward.to_dict())

            return new_available
        except UserNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao verificar recompensas: {str(e)}")

    # ========================================================================
    # ADMIN - Relatórios e Estatísticas
    # ========================================================================

    @staticmethod
    def get_reward_summary():
        """
        Obter resumo do sistema de recompensas (admin)

        Returns:
            dict: Estatísticas de recompensas
        """
        try:
            total_rewards = Reward.query.count()
            active_rewards = Reward.query.filter_by(is_active=True).count()
            inactive_rewards = total_rewards - active_rewards

            total_purchases = UserReward.query.count()
            total_redeemed = UserReward.query.filter_by(is_redeemed=True).count()
            pending_redeem = total_purchases - total_redeemed

            # Recompensas mais compradas
            most_purchased = db.session.query(
                Reward.id, Reward.name, db.func.count(UserReward.id).label('count')
            ).join(UserReward, Reward.id == UserReward.reward_id).group_by(
                Reward.id, Reward.name
            ).order_by(db.desc('count')).limit(5).all()

            most_purchased_data = [
                {'id': r[0], 'name': r[1], 'purchases': r[2]} for r in most_purchased
            ]

            # Total de coins gastos
            total_coins_spent = db.session.query(
                db.func.sum(Reward.coin_cost)
            ).join(UserReward, Reward.id == UserReward.reward_id).scalar() or 0

            return {
                'rewards': {
                    'total': total_rewards,
                    'active': active_rewards,
                    'inactive': inactive_rewards
                },
                'purchases': {
                    'total': total_purchases,
                    'redeemed': total_redeemed,
                    'pending': pending_redeem,
                    'total_coins_spent': total_coins_spent
                },
                'most_purchased': most_purchased_data
            }
        except Exception as e:
            raise Exception(f"Erro ao buscar resumo de recompensas: {str(e)}")

    @staticmethod
    def get_user_purchase_history(user_id):
        """
        Obter histórico de compras de um usuário (admin)

        Args:
            user_id: ID do usuário

        Returns:
            dict: Histórico de compras do usuário
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise UserNotFound(f"Usuário {user_id} não encontrado")

            user_rewards = UserReward.query.filter_by(user_id=user_id).order_by(
                UserReward.purchase_date.desc()
            ).all()

            total_spent = sum(
                ur.reward.coin_cost for ur in user_rewards if ur.reward
            )

            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'current_coins': user.coins
                },
                'total_spent': total_spent,
                'total_purchases': len(user_rewards),
                'purchases': [ur.to_dict() for ur in user_rewards]
            }
        except UserNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar histórico de compras: {str(e)}")