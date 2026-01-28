# PvP Система: Документация для Фронтенд Разработчика

## Обзор архитектуры

PvP система построена на WebSocket соединениях с использованием Django Channels и Redis для real-time коммуникации. Система включает в себя очередь, матчмейкинг, игровую сессию и рейтинг.

## WebSocket эндпоинты

### 1. Очередь и поиск матча
```
ws://127.0.0.1:8000/pvp/queue/
```
**Назначение**: Управление очередью и поиском противников

### 2. Игровая сессия
```
ws://127.0.0.1:8000/pvp/match/{match_id}/
```
**Назначение**: Real-time геймплей в конкретном матче

## API эндпоинты

### PvP управление
- `POST /api/pvp/find_match/` - Начать поиск матча
- `POST /api/pvp/cancel_search/` - Отменить поиск
- `GET /api/pvp/my_matches/` - История матчей
- `GET /api/pvp/rating/` - Текущий рейтинг

### Таблица лидеров
- `GET /api/pvp/leaderboard/` - Глобальный рейтинг
- Параметры: `subject_id` для фильтрации по предмету

## Статусы матчей

```typescript
enum MatchStatus {
    WAITING = "waiting",           // Ожидание игрока
    PLAYING = "playing",           // Идет игра  
    FINISHED = "finished",         // Завершен
    CANCELLED = "cancelled",       // Отменен
    TECHNICAL_ERROR = "technical_error" // Техническая ошибка
}
```

## Результаты матча

```typescript
enum MatchResult {
    PLAYER1_WIN = "player1_win",   // Победа игрока 1
    PLAYER2_WIN = "player2_win",   // Победа игрока 2
    DRAW = "draw",                 // Ничья
    TECHNICAL = "technical"        // Техническая ничья
}
```

## Процесс PvP сессии

### 1. Поиск матча

**Шаг 1**: Подключение к очереди
```javascript
const queueSocket = new WebSocket('ws://127.0.0.1:8000/pvp/queue/');
```

**Шаг 2**: Запуск поиска
```json
// Client → Server
{
    "type": "find_match",
    "subject_id": 1  // ID предмета (математика, физика и т.д.)
}
```

**Шаг 3**: Ответ сервера
```json
// Server → Client
{
    "type": "added_to_queue", 
    "subject": "Математика"
}
```

### 2. Нахождение противника

Когда найден противник:
```json
// Server → Client
{
    "type": "match_found",
    "match_id": 123,
    "subject": "Математика"
}
```

**Действия фронтенда**:
1. Закрыть соединение с очередью
2. Открыть соединение с матчем
3. Показать экран "Найден противник"

### 3. Игровая сессия

**Подключение к матчу**:
```javascript
const matchSocket = new WebSocket(`ws://127.0.0.1:8000/pvp/match/${matchId}/`);
```

**Запрос текущего задания**:
```json
// Client → Server
{"type": "get_task"}
```

**Ответ с заданием**:
```json
// Server → Client
{
    "type": "current_task",
    "task": {
        "id": 456,
        "description": "Решите уравнение: 2x + 5 = 15",
        "difficulty": "medium",
        "topics": ["algebra", "linear_equations"]
    }
}
```

**Отправка ответа**:
```json
// Client → Server
{
    "type": "submit_answer",
    "answer": "5"
}
```

**Результат ответа**:
```json
// Server → Client
{
    "type": "own_answer_result",
    "data": {
        "is_correct": true,
        "time_taken": 15.2,
        "tasks_solved": 3
    }
}
```

**Ответ противника**:
```json
// Server → Client
{
    "type": "opponent_answer", 
    "data": {
        "is_correct": false,
        "tasks_solved": 2,
        "total_tasks_in_match": 5
    }
}
```

### 4. Завершение матча

```json
// Server → Client
{
    "type": "match_finished",
    "result": "player1_win",
    "participants": [
        {
            "user_id": 1,
            "username": "Player1",
            "tasks_solved": 4,
            "time_taken": 180.5,
            "result": "win",
            "rating_change": +25
        },
        {
            "user_id": 2, 
            "username": "Player2",
            "tasks_solved": 2,
            "time_taken": 240.1,
            "result": "loss", 
            "rating_change": -25
        }
    ]
}
```

## Матчмейкинг система

### Алгоритм поиска противников

1. **Фильтр по предмету**: Только игроки с одинаковым `subject_id`
2. **Близость рейтинга**: Используется формула `Abs(rating1 - rating2)`
3. **Первый подходящий**: Выбирается игрок с минимальной разницей рейтинга

### Параметры матча

Настройки хранятся в `PvpSettings`:
- **Длительность**: По умолчанию 5 минут
- **Количество заданий**: Настраиваемое значение
- **Коэффициент ELO**: K-factor (по умолчанию 32)

## Рейтинговая система

### Формула ELO
```
new_rating = old_rating + k_factor * (actual_score - expected_score)
expected_score = 1 / (1 + 10^((opponent_rating - player_rating) / 400))
```

### Изменения рейтинга
- **Победа**: +K-factor ~ +32
- **Поражение**: -K-factor ~ -32  
- **Ничья**: Малые изменения
- **Техническая**: Без изменений

## Управление соединениями

### Аутентификация
WebSocket требует JWT токен в query параметрах:
```
ws://127.0.0.1:8000/pvp/queue/?token=your_jwt_token
```

### Обработка разрывов

- **Преднамеренный выход**: Отмена поиска, техническое поражение
- **Сбой соединения**: Автоматическое поражение
- **Возврат в матч**: Возможно до статуса `PLAYING`

## Данные для UI

### Статус в очереди
```json
{
    "in_queue": true,
    "subject": "Математика",
    "wait_time": 120,
    "players_searching": 15
}
```

### Прогресс в матче
```json
{
    "match_status": "playing",
    "time_remaining": 180,
    "current_task_index": 3,
    "total_tasks": 5,
    "my_progress": {
        "tasks_solved": 2,
        "current_task_time": 45.2
    },
    "opponent_progress": {
        "tasks_solved": 3
    }
}
```

## Рекомендуемая структура фронтенда

### Components
- `PvpQueueScreen` - Экран очереди
- `PvpMatchScreen` - Экран матча  
- `TaskComponent` - Компонент задания
- `ProgressIndicator` - Индикатор прогресса
- `CountdownTimer` - Таймер обратного отсчета
- `OpponentProgress` - Прогресс противника

### Services
- `PvpQueueService` - Управление очередью
- `PvpMatchService` - Управление матчем
- `WebSocketManager` - Обработка WebSocket соединений
- `RatingService` - Работа с рейтингом

### Store/State
```typescript
interface PvpState {
    queue: {
        isActive: boolean;
        subject: string | null;
        waitTime: number;
    };
    match: {
        id: number | null;
        status: MatchStatus;
        currentTask: Task | null;
        timeRemaining: number;
        myProgress: MatchProgress;
        opponentProgress: MatchProgress;
    };
    rating: {
        current: number;
        rank: string;
        change: number;
    };
}
```

## Важные моменты

1. **Последовательность заданий**: Задания выдаются последовательно, следующее доступно только после решения текущего
2. **Real-time обновления**: Все действия противника приходят мгновенно через WebSocket
3. **Таймер**: Общий таймер на матч, не зависит от скорости решения
4. **Технические результаты**: При разрыве соединения автоматически засчитывается поражение
5. **Рейтинг**: Обновляется сразу после окончания матча
6. **История**: Все матчи сохраняются и доступны через API

## Обработка ошибок

### Очередь
- `queue_full` - Очередь переполнена
- `already_in_queue` - Уже в очереди
- `subject_not_found` - Предмет не найден

### Матч
- `match_not_found` - Матч не найден
- `match_finished` - Матч уже завершен
- `invalid_answer` - Неверный формат ответа
- `task_timeout` - Время на задание истекло

Эта архитектура обеспечивает надежную и масштабируемую PvP систему с отличным пользовательским опытом.