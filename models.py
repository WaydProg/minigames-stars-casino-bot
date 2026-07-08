from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    balance = Column(Integer, default=0)
    total_bets = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    referral_code = Column(String(20), unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'))
    referrals_count = Column(Integer, default=0)
    referral_earnings = Column(Integer, default=0)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_bonus_at = Column(DateTime)  # Время последнего получения бонуса
    
    transactions = relationship("Transaction", back_populates="user")
    game_stats = relationship("GameStat", back_populates="user")
    user_bets = relationship("UserBet", back_populates="user")
    star_transactions = relationship("StarTransaction", back_populates="user")
    
    referrer = relationship("User", remote_side=[id], backref="referrals")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)  # 'deposit', 'withdraw', 'win', 'bet', 'referral'
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")

class GameStat(Base):
    __tablename__ = 'game_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_type = Column(String(20), nullable=False)
    bets_count = Column(Integer, default=0)
    wins_count = Column(Integer, default=0)
    total_bet = Column(Integer, default=0)
    total_win = Column(Integer, default=0)
    
    user = relationship("User", back_populates="game_stats")

class GameSetting(Base):
    __tablename__ = 'game_settings'
    
    id = Column(Integer, primary_key=True)
    game_type = Column(String(20), unique=True, nullable=False)
    win_chance = Column(Float, default=0.5)
    min_bet = Column(Integer, default=1)
    max_bet = Column(Integer, default=1000)
    cost = Column(Integer, default=5)
    win_multiplier = Column(Float, default=2.0)
    is_active = Column(Boolean, default=True)

class UserBet(Base):
    __tablename__ = 'user_bets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_type = Column(String(20), nullable=False)
    bet_amount = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="user_bets")

class StarTransaction(Base):
    __tablename__ = 'star_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')
    payload = Column(String(100), unique=True)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="star_transactions")

class WithdrawalRequest(Base):
    __tablename__ = 'withdrawal_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default='pending')
    message_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    user = relationship("User", backref="withdrawal_requests")

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    method = Column(String(20), default='stars')  # 'stars' или 'cryptobot'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="payment_methods")

class CryptobotPayment(Base):
    __tablename__ = 'cryptobot_payments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount_ton = Column(Float)  # Сумма в TON
    amount_stars = Column(Integer)  # Сумма в звездах
    invoice_id = Column(String(100))  # ID инвойса Cryptobot
    status = Column(String(20), default='pending')  # pending, paid, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)
    
    user = relationship("User", backref="cryptobot_payments")

class Promocode(Base):
    __tablename__ = 'promocodes'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)
    reward = Column(Integer)
    is_avaible = Column(Integer, default=1)
    avaible_until = Column(DateTime)

class use_of_promo_code(Base):
    __tablename__ = 'use_of_promo_codes'

    id = Column(Integer, primary_key=True)
    reward_id = Column(Integer, ForeignKey('promocodes.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
