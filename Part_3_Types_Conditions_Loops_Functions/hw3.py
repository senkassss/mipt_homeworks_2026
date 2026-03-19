#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
MONTHS_IN_YEAR = 12
INCOME_ARGS_COUNT = 3
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2

Date = tuple[int, int, int]
IncomeEntry = tuple[float, Date]
CostEntry = tuple[str, float, Date]
Categories = dict[str, float]


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return (year % 4) == 0


def date_key(date: Date) -> tuple[int, int, int]:
    day, month, year = date
    return year, month, day


def is_date_ordered_not_later(date: Date, limit: Date) -> bool:
    return date_key(date) <= date_key(limit)


def extract_date_parts(parts: list[str]) -> Date | None:
    day_raw, month_raw, year_raw = parts
    if not (day_raw.isdigit() and month_raw.isdigit() and year_raw.isdigit()):
        return None
    return int(day_raw), int(month_raw), int(year_raw)


def is_valid_month(month: int) -> bool:
    return 1 <= month <= MONTHS_IN_YEAR


def month_days(month: int, year: int) -> int:
    days = [
        31,
        29 if is_leap_year(year) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    return days[month - 1]


def is_valid_date(date: Date) -> bool:
    day, month, year = date
    if not is_valid_month(month):
        return False
    return 1 <= day <= month_days(month, year)


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None

    date = extract_date_parts(parts)
    if date is None:
        return None

    if not is_valid_date(date):
        return None

    return date


def parse_amount(value_raw: str) -> float | None:
    normalized = value_raw.replace(",", ".")
    dot_count = 0

    for symbol in normalized:
        if symbol == ".":
            dot_count += 1
            continue
        if not symbol.isdigit():
            return None

    if dot_count > 1:
        return None

    if normalized in {".", ""}:
        return None

    return float(normalized)


def to_display_amount(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def calculate_total_capital(
    date: Date,
    incomes: list[IncomeEntry],
    costs: list[CostEntry],
) -> float:
    total_income: float = 0
    total_cost: float = 0

    for amount, income_date in incomes:
        if is_date_ordered_not_later(income_date, date):
            total_income += amount

    for _, amount, cost_date in costs:
        if is_date_ordered_not_later(cost_date, date):
            total_cost += amount

    return total_income - total_cost


def is_in_month_period(item_date: Date, limit_date: Date) -> bool:
    item_key = date_key(item_date)
    limit_key = date_key(limit_date)
    if item_key[0] != limit_key[0]:
        return False
    if item_key[1] != limit_key[1]:
        return False
    return item_key[2] <= limit_key[2]


def calculate_month_income(date: Date, incomes: list[IncomeEntry]) -> float:
    month_income: float = 0
    for amount, income_date in incomes:
        if is_in_month_period(income_date, date):
            month_income += amount
    return month_income


def calculate_month_costs(
    date: Date,
    costs: list[CostEntry],
) -> tuple[float, Categories]:
    month_cost: float = 0
    categories: Categories = {}
    for category, amount, cost_date in costs:
        if is_in_month_period(cost_date, date):
            month_cost += amount
            categories[category] = categories.get(category, 0) + amount
    return month_cost, categories


def calculate_stats(
    date: Date,
    incomes: list[IncomeEntry],
    costs: list[CostEntry],
) -> tuple[float, float, float, Categories]:
    capital = calculate_total_capital(date, incomes, costs)
    month_income = calculate_month_income(date, incomes)
    month_cost, categories = calculate_month_costs(date, costs)
    return capital, month_income, month_cost, categories


def print_stats(
    date_raw: str,
    stats: tuple[float, float, float, Categories],
) -> None:
    month_diff = stats[1] - stats[2]

    print(f"Ваша статистика по состоянию на {date_raw}:")
    print(f"Суммарный капитал: {stats[0]:.2f} рублей")
    if month_diff >= 0:
        print(f"\u0412 этом месяце прибыль составила {month_diff:.2f} рублей")
    else:
        print(f"\u0412 этом месяце убыток составил {-month_diff:.2f} рублей")
    print(f"Доходы: {stats[1]:.2f} рублей")
    print(f"Расходы: {stats[2]:.2f} рублей")
    print()
    print("Детализация (категория: сумма):")
    if not stats[3]:
        return

    for index, category in enumerate(sorted(stats[3]), start=1):
        print(f"{index}. {category}: {to_display_amount(stats[3][category])}")


def handle_income(parts: list[str], incomes: list[IncomeEntry]) -> None:
    if len(parts) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(parts[1])
    if amount is None or amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    date = extract_date(parts[2])
    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    incomes.append((amount, date))
    print(OP_SUCCESS_MSG)


def handle_cost(parts: list[str], costs: list[CostEntry]) -> None:
    if len(parts) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(parts[2])
    if amount is None or amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    date = extract_date(parts[3])
    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    costs.append((parts[1], amount, date))
    print(OP_SUCCESS_MSG)


def handle_stats(
    parts: list[str],
    incomes: list[IncomeEntry],
    costs: list[CostEntry],
) -> None:
    if len(parts) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    date = extract_date(parts[1])
    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    print_stats(parts[1], calculate_stats(date, incomes, costs))


def process_command(
    parts: list[str],
    incomes: list[IncomeEntry],
    costs: list[CostEntry],
) -> None:
    if not parts:
        print(UNKNOWN_COMMAND_MSG)
        return

    command = parts[0]
    if command == "income":
        handle_income(parts, incomes)
        return
    if command == "cost":
        handle_cost(parts, costs)
        return
    if command == "stats":
        handle_stats(parts, incomes, costs)
        return
    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    incomes: list[IncomeEntry] = []
    costs: list[CostEntry] = []

    while True:
        raw_line = input()
        parts = raw_line.split()

        if not parts:
            print(UNKNOWN_COMMAND_MSG)
            continue

        process_command(parts, incomes, costs)


if __name__ == "__main__":
    main()
