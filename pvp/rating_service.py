from django.db import models
from django.contrib.auth import get_user_model
from pvp.models import Match, MatchParticipant, MatchResult, PvpSettings
from users.models import Rating
from decimal import Decimal, getcontext

User = get_user_model()

# Устанавливаем точность для Decimal
getcontext().prec = 10


class RatingService:
    """Сервис для работы с рейтингами"""
    
    @staticmethod
    def calculate_elo_rating(player1_rating, player2_rating, result, k_factor=32):
        """
        Рассчитывает новые рейтинги по системе Elo
        
        Args:
            player1_rating: Рейтинг первого игрока
            player2_rating: Рейтинг второго игрока
            result: Результат матча ('win', 'loss', 'draw', 'technical')
            k_factor: K-фактор (по умолчанию 32)
        
        Returns:
            tuple: (new_player1_rating, new_player2_rating)
        """
        if result == 'technical':
            # При технической ошибке рейтинги не меняются
            return player1_rating, player2_rating
        
        # Конвертируем в float для расчетов
        r1 = float(player1_rating)
        r2 = float(player2_rating)
        
        # Рассчитываем ожидаемые результаты
        expected1 = RatingService._expected_score(r1, r2)
        expected2 = 1 - expected1
        
        # Определяем фактические результаты
        if result == 'player1_win':
            actual1, actual2 = 1.0, 0.0
        elif result == 'player2_win':
            actual1, actual2 = 0.0, 1.0
        else:  # draw
            actual1, actual2 = 0.5, 0.5
        
        # Рассчитываем новые рейтинги
        new_player1_rating = round(r1 + k_factor * (actual1 - expected1))
        new_player2_rating = round(r2 + k_factor * (actual2 - expected2))
        
        return int(new_player1_rating), int(new_player2_rating)
    
    @staticmethod
    def _expected_score(rating1, rating2):
        """Рассчитывает ожидаемый результат для игрока 1"""
        r1 = float(rating1)
        r2 = float(rating2)
        return 1 / (1 + 10 ** ((r2 - r1) / 400))
    
    @staticmethod
    def update_match_ratings(match_id):
        """
        Обновляет рейтинги после завершения матча
        
        Args:
            match_id: ID матча
        """
        try:
            match = Match.objects.get(id=match_id)
            
            if match.status != 'finished' or not match.result:
                return False
            
            participants = list(match.participants.all())
            if len(participants) != 2:
                return False
            
            # Получаем текущие рейтинги
            rating1, _ = Rating.objects.get_or_create(user=participants[0].user)
            rating2, _ = Rating.objects.get_or_create(user=participants[1].user)
            
            # Получаем K-фактор из настроек
            settings = PvpSettings.objects.filter(is_active=True).first()
            k_factor = settings.k_factor if settings else 32
            
            # Рассчитываем новые рейтинги
            old_rating1 = rating1.score
            old_rating2 = rating2.score
            
            new_rating1, new_rating2 = RatingService.calculate_elo_rating(
                old_rating1, old_rating2, match.result, k_factor
            )
            
            # Обновляем рейтинги
            rating1.score = new_rating1
            rating2.score = new_rating2
            
            # Обновляем статистику
            rating1.matches_played += 1
            rating2.matches_played += 1
            
            if match.result == 'player1_win':
                rating1.matches_won += 1
                rating2.matches_lost += 1
            elif match.result == 'player2_win':
                rating1.matches_lost += 1
                rating2.matches_won += 1
            elif match.result == 'draw':
                rating1.matches_drawn += 1
                rating2.matches_drawn += 1
            # При technical не обновляем статистику
            
            rating1.save()
            rating2.save()
            
            return True
            
        except Match.DoesNotExist:
            return False
    
    @staticmethod
    def get_leaderboard(limit=50, subject_id=None):
        """
        Получает таблицу лидеров
        
        Args:
            limit: Максимальное количество записей
            subject_id: Фильтр по предмету (опционально)
        
        Returns:
            list: Список с данными для таблицы лидеров
        """
        queryset = Rating.objects.select_related('user').all()
        
        # Фильтрация по предмету
        if subject_id:
            queryset = queryset.filter(
                user__matchparticipant__match__subject_id=subject_id
            ).distinct()
        
        # Сортировка по рейтингу и ограничение
        leaderboard = []
        rank = 1
        
        for rating in queryset.order_by('-score')[:limit]:
            win_rate = 0.0
            if rating.matches_played > 0:
                win_rate = (rating.matches_won / rating.matches_played) * 100
            
            leaderboard.append({
                'rank': rank,
                'user_id': rating.user.id,
                'username': rating.user.username,
                'rating': rating.score,
                'matches_played': rating.matches_played,
                'matches_won': rating.matches_won,
                'matches_lost': rating.matches_lost,
                'matches_drawn': rating.matches_drawn,
                'win_rate': round(win_rate, 2)
            })
            rank += 1
        
        return leaderboard
    
    @staticmethod
    def get_user_rating_history(user_id, limit=20):
        """
        Получает историю изменений рейтинга пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
        
        Returns:
            list: Список с историей рейтинга
        """
        try:
            user = User.objects.get(id=user_id)
            
            matches = Match.objects.filter(
                participants__user=user,
                status='finished'
            ).order_by('-finished_at')[:limit]
            
            history = []
            current_rating = 1000  # Начальный рейтинг
            
            for match in reversed(matches):  # От старых к новым
                participant = match.participants.get(user=user)
                
                # Получаем рейтинг на момент матча
                rating = Rating.objects.get(user=user)
                
                history.append({
                    'match_id': match.id,
                    'subject': match.subject.name,
                    'result': match.result,
                    'rating_change': 0,  # TODO: Рассчитать изменение
                    'new_rating': rating.score,
                    'date': match.finished_at,
                    'tasks_solved': participant.tasks_solved,
                    'opponent': None  # TODO: Добавить информацию о сопернике
                })
            
            return history
            
        except User.DoesNotExist:
            return []
    
    @staticmethod
    def get_rating_stats(user_id, subject_id=None):
        """
        Получает детальную статистику рейтинга пользователя
        
        Args:
            user_id: ID пользователя
            subject_id: Фильтр по предмету (опционально)
        
        Returns:
            dict: Статистика пользователя
        """
        try:
            user = User.objects.get(id=user_id)
            rating, _ = Rating.objects.get_or_create(user=user)
            
            # Базовый запрос матчей
            matches_query = Match.objects.filter(
                participants__user=user,
                status='finished'
            )
            
            if subject_id:
                matches_query = matches_query.filter(subject_id=subject_id)
            
            total_matches = matches_query.count()
            wins = matches_query.filter(result='player1_win').filter(
                participants__user=user, participants__player_number=1
            ).count() + matches_query.filter(result='player2_win').filter(
                participants__user=user, participants__player_number=2
            ).count()
            
            losses = matches_query.filter(result='player2_win').filter(
                participants__user=user, participants__player_number=1
            ).count() + matches_query.filter(result='player1_win').filter(
                participants__user=user, participants__player_number=2
            ).count()
            
            draws = matches_query.filter(result='draw').count()
            
            # Рассчитываем средний рейтинг оппонентов
            opponent_ratings = []
            for match in matches_query:
                opponent_participant = match.participants.exclude(user=user).first()
                if opponent_participant:
                    opponent_rating, _ = Rating.objects.get_or_create(user=opponent_participant.user)
                    opponent_ratings.append(opponent_rating.score)
            
            avg_opponent_rating = sum(opponent_ratings) / len(opponent_ratings) if opponent_ratings else 0
            
            return {
                'current_rating': rating.score,
                'total_matches': total_matches,
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'win_rate': round((wins / total_matches) * 100, 2) if total_matches > 0 else 0,
                'average_opponent_rating': round(avg_opponent_rating, 2),
                'peak_rating': rating.score,  # TODO: Реализовать пиковый рейтинг
                'lowest_rating': rating.score  # TODO: Реализовать минимальный рейтинг
            }
            
        except User.DoesNotExist:
            return None