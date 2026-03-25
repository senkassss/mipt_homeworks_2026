#!/usr/bin/env python

import sys
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
MONTHS_IN_YEAR = 12
INCOME_COMMAND_PARTS = 3
COST_COMMAND_PARTS = 4
STATS_COMMAND_PARTS = 2
ZERO_AMOUNT = 0.0
MIN_DAY = 1
MIN_MONTH = 1
SPLIT_MARKER = "::"
DATE_SEPARATOR = "-"
DATE_KEY = "date"
AMOUNT_KEY = "amount"
CATEGORY_KEY = "category"

Date = tuple[int, int, int]
Transaction = dict[str, Any]
CategoriesTotals = dict[str, float]
StatDelta = tuple[float, float]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[Transaction] = []


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return (year % 4) == 0


def parse_date_parts(parts: list[str]) -> Date | None:
    if not all(part.isdigit() for part in parts):
        return None
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    return day, month, year


def month_days(month: int, year: int) -> int:
    days_per_month = (
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
    )
    return days_per_month[month - 1]


def is_valid_date(date: Date) -> bool:
    day, month, year = date
    if month < MIN_MONTH or month > MONTHS_IN_YEAR:
        return False
    max_day = month_days(month, year)
    return MIN_DAY <= day <= max_day


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split(DATE_SEPARATOR)
    if len(parts) != DATE_PARTS_COUNT:
        return None

    parsed_parts = parse_date_parts(parts)
    if parsed_parts is None:
        return None

    if not is_valid_date(parsed_parts):
        return None
    return parsed_parts


def date_less_than(left: Date, right: Date) -> bool:
    left_day, left_month, left_year = left
    right_day, right_month, right_year = right
    left_date = (left_year, left_month, left_day)
    right_date = (right_year, right_month, right_day)
    return left_date < right_date


def is_valid_category(category_name: str) -> bool:
    if SPLIT_MARKER not in category_name:
        return False
    common_category, target_category = category_name.split(
        SPLIT_MARKER,
        maxsplit=1,
    )
    if common_category not in EXPENSE_CATEGORIES:
        return False
    return target_category in EXPENSE_CATEGORIES[common_category]


def append_empty_record() -> None:
    financial_transactions_storage.append({})


def income_handler(amount: float, income_date: str) -> str:
    if amount <= ZERO_AMOUNT:
        append_empty_record()
        return NONPOSITIVE_VALUE_MSG

    parsed_income_date = extract_date(income_date)
    if parsed_income_date is None:
        append_empty_record()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {AMOUNT_KEY: amount, DATE_KEY: parsed_income_date},
    )
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= ZERO_AMOUNT:
        append_empty_record()
        return NONPOSITIVE_VALUE_MSG

    parsed_income_date = extract_date(income_date)
    if parsed_income_date is None:
        append_empty_record()
        return INCORRECT_DATE_MSG

    if not is_valid_category(category_name):
        append_empty_record()
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append(
        {
            CATEGORY_KEY: category_name,
            AMOUNT_KEY: amount,
            DATE_KEY: parsed_income_date,
        },
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    categories: list[str] = []
    for category, subs in EXPENSE_CATEGORIES.items():
        categories.extend(f"{category}{SPLIT_MARKER}{sub}" for sub in subs)
    return "\n".join(categories)


def parse_storage_date(date_data: Any) -> Date | None:
    if isinstance(date_data, tuple) and len(date_data) == DATE_PARTS_COUNT:
        return date_data
    if isinstance(date_data, str):
        return extract_date(date_data)
    return None


def can_use_operation_date(
    operation_data: Transaction,
    report_date: Date,
) -> bool:
    if DATE_KEY not in operation_data:
        return False
    operation_date = parse_storage_date(operation_data[DATE_KEY])
    if operation_date is None:
        return False
    return date_less_than(operation_date, report_date)


def resolve_operation_amount(operation_data: Transaction) -> float:
    amount_raw = operation_data.get(AMOUNT_KEY, ZERO_AMOUNT)
    return float(amount_raw)


def update_category_total(
    category_details: CategoriesTotals,
    category: str,
    amount: float,
) -> None:
    previous_category_amount = category_details.get(category, ZERO_AMOUNT)
    category_details[category] = round(previous_category_amount + amount, 2)


def collect_stats(
    report_date: Date,
) -> tuple[float, float, CategoriesTotals]:
    total_income = ZERO_AMOUNT
    total_cost = ZERO_AMOUNT
    category_details: CategoriesTotals = {}

    for operation_data in financial_transactions_storage:
        if not can_use_operation_date(operation_data, report_date):
            continue

        income_change, cost_change = collect_operation_stats(
            operation_data,
            category_details,
        )
        total_income += income_change
        total_cost += cost_change

    return total_income, total_cost, category_details


def collect_operation_stats(
    operation_data: Transaction,
    category_details: CategoriesTotals,
) -> StatDelta:
    amount = resolve_operation_amount(operation_data)
    category_raw = operation_data.get(CATEGORY_KEY)
    if isinstance(category_raw, str):
        update_category_total(category_details, category_raw, amount)
        return ZERO_AMOUNT, amount
    return amount, ZERO_AMOUNT


def format_categories(category_details: CategoriesTotals) -> str:
    category_lines: list[str] = []
    for index, (category, amount) in enumerate(category_details.items()):
        category_lines.append(f"{index}. {category}: {amount}")
    return "\n".join(category_lines)


def stats_handler(report_date: str) -> str:
    parsed_report_date = extract_date(report_date)
    if parsed_report_date is None:
        return INCORRECT_DATE_MSG

    total_income, total_cost, category_details = collect_stats(
        parsed_report_date,
    )

    rounded_cost = round(total_cost, 2)
    rounded_income = round(total_income, 2)
    total_capital = round(rounded_cost - rounded_income, 2)
    amount_word = "loss" if total_capital < 0 else "profit"
    category_details_stat = format_categories(category_details)

    return (
        f"Your statistics as of {report_date}:\n"
        f"Total capital: {total_capital} rubles\n"
        f"This month, the {amount_word} amounted to {total_capital} rubles.\n"
        f"Income: {rounded_cost} rubles\n"
        f"Expenses: {rounded_income} rubles\n\n"
        f"Details (category: amount):\n"
        f"{category_details_stat}\n"
    )


def parse_amount(amount_raw: str) -> float | None:
    normalized_amount = amount_raw.replace(",", ".")
    if normalized_amount.count(".") > 1:
        return None

    candidate = normalized_amount.replace(".", "", 1)
    if not candidate.isdigit():
        return None
    return float(normalized_amount)


def is_cost_categories_command(parts: list[str], command: str) -> bool:
    if command != "cost":
        return False
    if len(parts) != STATS_COMMAND_PARTS:
        return False
    return parts[1] == "categories"


def process_income_command(parts: list[str]) -> str:
    if len(parts) != INCOME_COMMAND_PARTS:
        return UNKNOWN_COMMAND_MSG
    parsed_amount = parse_amount(parts[1])
    if parsed_amount is None:
        return NONPOSITIVE_VALUE_MSG
    return income_handler(parsed_amount, parts[2])


def process_cost_command(parts: list[str]) -> str:
    if len(parts) == STATS_COMMAND_PARTS and parts[1] == "categories":
        return cost_categories_handler()
    if len(parts) != COST_COMMAND_PARTS:
        return UNKNOWN_COMMAND_MSG
    parsed_amount = parse_amount(parts[2])
    if parsed_amount is None:
        return NONPOSITIVE_VALUE_MSG
    return cost_handler(parts[1], parsed_amount, parts[3])


def process_stats_command(parts: list[str]) -> str:
    if len(parts) != STATS_COMMAND_PARTS:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(parts[1])


def process_command(parts: list[str]) -> str:
    command = parts[0]
    if command == "income":
        return process_income_command(parts)
    if command == "cost":
        return process_cost_command(parts)
    if command == "stats":
        return process_stats_command(parts)
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    for raw_line in sys.stdin:
        stripped_line = raw_line.strip()
        if not stripped_line:
            print(UNKNOWN_COMMAND_MSG)
            continue

        parts = stripped_line.split()
        print(process_command(parts))


if __name__ == "__main__":
    main()
