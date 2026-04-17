import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


@dataclass
class _State:
    failed_count: int = 0
    block_time: datetime | None = None


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        errors: list[ValueError] = []
        if not _is_positive_int(critical_count):
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not _is_positive_int(time_to_recover):
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

    def __call__(
        self,
        func: CallableWithMeta[P, R_co],
    ) -> CallableWithMeta[P, R_co]:
        state = _State()
        func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._ensure_not_blocked(state=state, func_name=func_name)

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                self._process_error(
                    state=state,
                    func_name=func_name,
                    error=error,
                )
                raise

            state.failed_count = 0
            return result

        return wrapper

    def _ensure_not_blocked(self, state: _State, func_name: str) -> None:
        if state.block_time is None:
            return
        recover_at = state.block_time + timedelta(seconds=self.time_to_recover)
        if datetime.now(UTC) >= recover_at:
            state.block_time = None
            state.failed_count = 0
            return
        raise BreakerError(func_name=func_name, block_time=state.block_time)

    def _process_error(
        self,
        state: _State,
        func_name: str,
        error: Exception,
    ) -> None:
        if not isinstance(error, self.triggers_on):
            return
        state.failed_count += 1
        if state.failed_count < self.critical_count:
            return
        state.block_time = datetime.now(UTC)
        raise BreakerError(
            func_name=func_name,
            block_time=state.block_time,
        ) from error


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(
        f"https://jsonplaceholder.typicode.com/comments?postId={post_id}",
    )
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
