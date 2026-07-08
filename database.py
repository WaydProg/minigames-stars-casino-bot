from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import select, update, delete
from models import Base, User, Transaction, GameStat, GameSetting, UserBet, WithdrawalRequest, CryptobotPayment, Promocode, use_of_promo_code
from config import GAME_SETTINGS, GAME_COSTS, WIN_MULTIPLIERS
import asyncio
import uuid
from datetime import datetime

class Database:
    def __init__(self, db_url='sqlite+aiosqlite:///casino.db'):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._create_default_settings()

    async def _create_default_settings(self):
        async with self.async_session() as session:
            games = ['dice', 'dart', 'basketball', 'football', 'bowling', 'slot']
            
            for game in games:
                result = await session.execute(
                    select(GameSetting).where(GameSetting.game_type == game)
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    session.add(GameSetting(
                        game_type=game,
                        win_chance=GAME_SETTINGS.get(f"{game}_win_chance", 0.5),
                        min_bet=GAME_SETTINGS.get("min_bet", 1),
                        max_bet=GAME_SETTINGS.get("max_bet", 1000),
                        cost=GAME_COSTS.get(game, 5),
                        win_multiplier=WIN_MULTIPLIERS.get(game, 2.0)
                    ))
            await session.commit()

    async def get_user(self, user_id: int):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            return user
        
    async def get_user_by_username(self, username: int):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            return user

    async def get_user_by_id(self, id: int):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.id == id))
            user = result.scalar_one_or_none()
            return user

    async def create_user(self, user_id: int, username: str, first_name: str, last_name: str = None, referred_by: int = None):
        async with self.async_session() as session:
            # Проверяем, не существует ли уже пользователь
            result = await session.execute(select(User).where(User.user_id == user_id))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                return existing_user
        
        # Генерируем уникальный реферальный код
            import random
            import string
        
            while True:
                referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                result = await session.execute(select(User).where(User.referral_code == referral_code))
                if not result.scalar_one_or_none():
                    break
        
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referral_code=referral_code,
                referred_by=referred_by
            )
            session.add(user)
            await session.commit()
        
        # Если есть реферер, обновляем его статистику
            if referred_by:
                referrer_result = await session.execute(select(User).where(User.id == referred_by))
                referrer = referrer_result.scalar_one_or_none()
                if referrer:
                    referrer.referrals_count += 1
                    await session.commit()
        
            return user

    async def update_balance(self, user_id: int, amount: int, tr_type: str, description: str = None):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                user.balance += amount
                
                # Создаем транзакцию
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type=tr_type,
                    description=description
                )
                session.add(transaction)
                
                await session.commit()
                return user.balance
        return None

    async def get_game_setting(self, game_type: str):
        async with self.async_session() as session:
            result = await session.execute(select(GameSetting).where(GameSetting.game_type == game_type))
            setting = result.scalar_one_or_none()
            return setting

    async def update_game_setting(self, game_type: str, **kwargs):
        async with self.async_session() as session:
            result = await session.execute(select(GameSetting).where(GameSetting.game_type == game_type))
            setting = result.scalar_one_or_none()
            
            if setting:
                for key, value in kwargs.items():
                    if hasattr(setting, key):
                        setattr(setting, key, value)
                await session.commit()
                return setting
        return None

    async def update_game_stat(self, user_id: int, game_type: str, bet_amount: int, win_amount: int = 0):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                # Обновляем общую статистику пользователя
                user.total_bets += 1
                if win_amount > 0:
                    user.total_wins += 1

                # Обновляем статистику по конкретной игре
                result = await session.execute(
                    select(GameStat).where(
                        GameStat.user_id == user.id,
                        GameStat.game_type == game_type
                    )
                )
                game_stat = result.scalar_one_or_none()
                
                if not game_stat:
                    game_stat = GameStat(
                        user_id=user.id,
                        game_type=game_type,
                        bets_count=1,
                        wins_count=1 if win_amount > 0 else 0,
                        total_bet=bet_amount,
                        total_win=win_amount
                    )
                    session.add(game_stat)
                else:
                    game_stat.bets_count += 1
                    game_stat.total_bet += bet_amount
                    game_stat.total_win += win_amount
                    if win_amount > 0:
                        game_stat.wins_count += 1

                await session.commit()

    async def get_all_users(self):
        async with self.async_session() as session:
            result = await session.execute(select(User))
            return result.scalars().all()

    async def get_all_settings(self):
        async with self.async_session() as session:
            result = await session.execute(select(GameSetting))
            return result.scalars().all()

    async def add_stars_to_user(self, username: int, amount: int):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if user:
                user.balance += amount
                
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type="deposit",
                    description="Администратор добавил звезды"
                )
                session.add(transaction)
                
                await session.commit()
                return user.balance
        return None

    async def get_user_bet(self, user_id: int, game_type: str):
        async with self.async_session() as session:
            result = await session.execute(
                select(UserBet).join(User).where(
                    User.user_id == user_id,
                    UserBet.game_type == game_type
                )
            )
            user_bet = result.scalar_one_or_none()
            return user_bet

    async def set_user_bet(self, user_id: int, game_type: str, bet_amount: int):
        async with self.async_session() as session:
            # Получаем пользователя
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Получаем настройки игры для проверки лимитов
            result = await session.execute(select(GameSetting).where(GameSetting.game_type == game_type))
            setting = result.scalar_one_or_none()
            
            if not setting:
                return None
            
            # Проверяем лимиты ставок
            if bet_amount < setting.min_bet or bet_amount > setting.max_bet:
                return False
            
            # Ищем существующую ставку пользователя
            result = await session.execute(
                select(UserBet).where(
                    UserBet.user_id == user.id,
                    UserBet.game_type == game_type
                )
            )
            user_bet = result.scalar_one_or_none()
            
            if user_bet:
                user_bet.bet_amount = bet_amount
            else:
                user_bet = UserBet(
                    user_id=user.id,
                    game_type=game_type,
                    bet_amount=bet_amount
                )
                session.add(user_bet)
            
            await session.commit()
            return True

    async def get_effective_bet_amount(self, user_id: int, game_type: str):
        async with self.async_session() as session:
            # Получаем пользовательскую ставку
            result = await session.execute(
                select(UserBet).join(User).where(
                    User.user_id == user_id,
                    UserBet.game_type == game_type
                )
            )
            user_bet = result.scalar_one_or_none()
            
            # Получаем стандартную ставку игры
            result = await session.execute(select(GameSetting).where(GameSetting.game_type == game_type))
            setting = result.scalar_one_or_none()
            
            if not setting:
                return 0
            
            # Возвращаем пользовательскую ставку если есть, иначе стандартную
            if user_bet and user_bet.bet_amount > 0:
                return user_bet.bet_amount
            else:
                return setting.cost

    async def get_recent_games(self, limit: int = 10):
        async with self.async_session() as session:
            # Получаем последние транзакции ставок и выигрышей
            result = await session.execute(
                select(Transaction)
                .join(User)
                .where(Transaction.type.in_(['bet', 'win']))
                .order_by(Transaction.created_at.desc())
                .limit(limit)
            )
            transactions = result.scalars().all()
            
            games_history = []
            for transaction in transactions:
                user_result = await session.execute(select(User).where(User.id == transaction.user_id))
                user = user_result.scalar_one_or_none()
                
                if user:
                    game_type = "unknown"
                    if 'dice' in transaction.description:
                        game_type = "dice"
                    elif 'dart' in transaction.description:
                        game_type = "dart"
                    elif 'basketball' in transaction.description:
                        game_type = "basketball"
                    elif 'football' in transaction.description:
                        game_type = "football"
                    elif 'bowling' in transaction.description:
                        game_type = "bowling"
                    elif 'slot' in transaction.description:
                        game_type = "slot"
                    
                    games_history.append({
                        'user_id': user.user_id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'game_type': game_type,
                        'amount': transaction.amount,
                        'type': transaction.type,
                        'description': transaction.description,
                        'created_at': transaction.created_at
                    })
            
            return games_history

    async def create_withdrawal_request(self, user_id: int, amount: int):
        async with self.async_session() as session:
            # Получаем пользователя по user_id
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
        
            if not user:
                return None
        
            withdrawal = WithdrawalRequest(
                user_id=user.id,  # Используем внутренний id пользователя
                amount=amount,
                status='pending'
            )
            session.add(withdrawal)
            await session.commit()
        
            # Перезагружаем объект с joinedload
            result = await session.execute(
             select(WithdrawalRequest)
                .options(joinedload(WithdrawalRequest.user))
                .where(WithdrawalRequest.id == withdrawal.id)
            )
            return result.scalar_one_or_none()

    async def get_withdrawal_request(self, request_id: int):
        async with self.async_session() as session:
            result = await session.execute(
                select(WithdrawalRequest)
                .options(joinedload(WithdrawalRequest.user))
                .where(WithdrawalRequest.id == request_id)
            )   
            return result.scalar_one_or_none()

    async def update_withdrawal_request(self, request_id: int, status: str, message_id: int = None):
        async with self.async_session() as session:
            result = await session.execute(
                select(WithdrawalRequest).where(WithdrawalRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if request:
                request.status = status
                if message_id:
                    request.message_id = message_id
                if status in ['approved', 'rejected']:
                    request.processed_at = datetime.utcnow()
                await session.commit()
                return request
        return None

    async def get_pending_withdrawals(self):
        async with self.async_session() as session:
            result = await session.execute(
                select(WithdrawalRequest)
                .where(WithdrawalRequest.status == 'pending')
                .order_by(WithdrawalRequest.created_at.asc())
            )
            return result.scalars().all()

    async def get_user_withdrawals(self, user_id: int, limit: int = 10):
        async with self.async_session() as session:
            result = await session.execute(
                select(WithdrawalRequest)
                .join(User)
                .where(User.user_id == user_id)
                .order_by(WithdrawalRequest.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def create_user(self, user_id: int, username: str, first_name: str, last_name: str = None, referred_by: int = None):
        async with self.async_session() as session:
            # Генерируем уникальный реферальный код
            import random
            import string
        
            while True:
                referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                result = await session.execute(select(User).where(User.referral_code == referral_code))
                if not result.scalar_one_or_none():
                    break
        
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referral_code=referral_code,
                referred_by=referred_by
            )
            session.add(user)
            await session.commit()
        
            # Если есть реферер, обновляем его статистику
            if referred_by:
                referrer_result = await session.execute(select(User).where(User.id == referred_by))
                referrer = referrer_result.scalar_one_or_none()
                if referrer:
                    referrer.referrals_count += 1
                    await session.commit()
        
            return user

    async def get_user_by_referral_code(self, referral_code: str):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.referral_code == referral_code))
            return result.scalar_one_or_none()

    async def add_referral_earnings(self, user_id: int, amount: int):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
        
            if user:
                user.referral_earnings += amount
                user.balance += amount
            
                transaction = Transaction(
                    user_id=user.id,
                    amount=amount,
                    type="referral",
                    description=f"Реферальное вознаграждение: {amount} звезд"
                )
                session.add(transaction)
            
                await session.commit()
                return user.balance
            return None

    async def get_user_referrals(self, id: int):
        async with self.async_session() as session:
            result = await session.execute(
                select(User)
                .where(User.referred_by == id)
                .order_by(User.registered_at.desc())
            )
            return result.scalars().all()

    async def get_user_by_referral_code(self, referral_code: str):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.referral_code == referral_code))
            return result.scalar_one_or_none()
    
    async def create_cryptobot_payment(self, user_id: int, amount_ton: float, amount_stars: int, invoice_id: str):
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()
        
            if not user:
                return None
        
            payment = CryptobotPayment(
                user_id=user.id,
                amount_ton=amount_ton,
                amount_stars=amount_stars,
                invoice_id=invoice_id,
                status='pending'
            )
            session.add(payment)
            await session.commit()
            return payment

    async def get_last_cryptobot_payment(self, user_id: int):
        async with self.async_session() as session:
            result = await session.execute(
                select(CryptobotPayment)
                .join(User)
                .where(User.user_id == user_id)
                .where(CryptobotPayment.status == 'pending')
                .order_by(CryptobotPayment.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def update_cryptobot_payment(self, payment_id: int, status: str):
        async with self.async_session() as session:
            result = await session.execute(
                select(CryptobotPayment).where(CryptobotPayment.id == payment_id)
            )
            payment = result.scalar_one_or_none()
        
            if payment:
                payment.status = status
                if status == 'paid':
                    payment.paid_at = datetime.utcnow()
                await session.commit()
                return payment
            return None

    async def can_claim_daily_bonus(self, user_id: int):
        """Проверяет, может ли пользователь получить ежедневный бонус"""
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.last_bonus_at:
                return True

            from datetime import datetime, timedelta
            now = datetime.utcnow()
            time_since_last_bonus = now - user.last_bonus_at

            # Бонус можно получать раз в 24 часа
            return time_since_last_bonus >= timedelta(hours=24)

    async def claim_daily_bonus(self, user_id: int):
        """Выдает ежедневный бонус пользователю"""
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return None

            bonus_amount = 5
            user.balance += bonus_amount
            user.last_bonus_at = datetime.utcnow()

            # Создаем транзакцию
            transaction = Transaction(
                user_id=user.id,
                amount=bonus_amount,
                type="bonus",
                description=f"Ежедневный бонус: {bonus_amount} звезд"
            )
            session.add(transaction)

            await session.commit()
            return user.balance

    async def add_promo_to_db(self, name: str, code: str, reward: int, available_until: str):
        """Добавление прокода в бд"""
        async with self.async_session() as session:
            result = await session.execute(select(Promocode).where(Promocode.code == code))
            promo = result.scalar_one_or_none()
            if promo:
                raise ValueError(f"Промокод с кодом '{code}' уже существует")
            
            promocode = Promocode(
                name=name,
                code=code,
                reward=reward,
                available_until=available_until
            )
            session.add(promocode)
            await session.commit()
            return True
        
    async def get_promocodes(self):
        """Получение всех промокодов"""
        async with self.async_session() as session:
            result = await session.execute(select(Promocode))
            return result.scalars().all()
    
    async def get_promocode_by_code(self, code):
        """Получение конкретного промокода"""
        async with self.async_session() as session:
            result = await session.execute(select(Promocode).where(Promocode.code == code))
            return result.scalar_one_or_none()
        
    async def switch_available_promo(self, promo_id):
        async with self.async_session() as session:
            stmt = (
                update(Promocode)
                .where(Promocode.id == promo_id)
                .values(is_available=0)
                .returning(Promocode.id)
            )
            result = await session.execute(stmt)
            await session.commit()
            updated = result.scalar()
            if updated is None:
                raise ValueError(f'Промокод с id {promo_id} не найден')
            return True
    
    async def delete_promo(self, promo_id):
        async with self.async_session() as session:
            result = await session.get(Promocode, promo_id)
            
            if not result:
                raise ValueError('❌ Промокод не найден')
            
            await session.delete(result)
            await session.commit()

            return True
        
    async def add_use_promo(self, user_id, promo_id):
        async with self.async_session() as session:
            result = await session.scalar(select(use_of_promo_code).where(use_of_promo_code.promo_id == promo_id and use_of_promo_code.user_id == user_id))

            if result:
                raise ValueError('❌ Промокод уже применён')
            
            session.add(use_of_promo_code(
                promo_id=promo_id,
                user_id=user_id
            ))
            await session.commit()
            
            return True
            
    # Глобальный экземпляр базы данных
db = Database()