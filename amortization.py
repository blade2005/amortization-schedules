#!/usr/bin/env python3
import csv
import numpy as np
import json
import argparse
import math
import datetime


def parse_opts():
    """Parse CLI options"""
    parser = argparse.ArgumentParser(
        description="Given Balance, Monthly Payment and an interest rate calculate how many months to pay off a loan"
    )
    parser.add_argument(
        "--balance",
        "-b",
        action="store",
        help="Current Balance",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--monthly",
        "-m",
        action="store",
        help="Monthly Payment Amount",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--interest",
        "-i",
        action="store",
        help="Interest Rate as decimal",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        help="File to output to",
        default="amortization.csv",
    )
    parser.add_argument(
        "--extra", "-e", action="append", help="Extra payment", type=json.loads
    )
    parser.add_argument(
        "--change-payment",
        "-c",
        action="append",
        help="Change Monthly payment amount",
        type=json.loads,
    )
    args = vars(parser.parse_args())
    if args["interest"] > 1:
        parser.error("Your interest rate should be between 0 and 1.")
    if args["monthly"] > 0:
        parser.error("Your monthly payment should be entered in the negative")
    if args["extra"]:
        args["extra"] = {
            datetime.date.fromisoformat(extra_payment["month"]): extra_payment[
                "payment"
            ]
            for extra_payment in args["extra"]
        }
    if args["change_payment"]:
        args["change_payment"] = {
            datetime.date.fromisoformat(extra_payment["month"]): extra_payment[
                "payment"
            ]
            for extra_payment in args["change_payment"]
        }

    return args


def calculate_months(interest, monthly, balance):
    months = math.ceil(np.nper(interest / 12, monthly, balance))
    print("Your loan will take {} months to pay off.".format(months))
    return months


def _change_payment(args, month_date):
    payment = args["monthly"]
    if args["change_payment"]:
        for change in args["change_payment"]:
            if month_date == change:
                payment = args["monthly"] = args["change_payment"][change]
    return payment


def _principal(args, month_date, interest, payment):
    principal = args["monthly"] - interest

    if args["extra"]:
        for extra_month in args["extra"]:
            if month_date == extra_month:
                principal = args["extra"][extra_month] - interest
                payment = args["extra"][extra_month]
    return principal, interest, payment


def amortization_schedule(months, args):
    month_balance = args["balance"]
    cur = datetime.date.today().replace(day=1)
    rows = []
    for period in range(1, months + 1):
        month_date = (cur + datetime.timedelta(days=31 * period)).replace(day=1)

        principal, interest, payment = _principal(
            args,
            month_date,
            np.ipmt(args["interest"] / 12, period, months, month_balance),
            _change_payment(args, month_date),
        )

        month_balance = month_balance + principal
        rows.append(
            [
                "{}/{}".format(month_date.year, month_date.month),
                period,
                payment,
                interest.round(2),
                principal.round(2),
                round(month_balance, 2),
            ]
        )
        if month_balance < 0:
            break
    return rows


def main():
    args = parse_opts()
    months = calculate_months(args["interest"], args["monthly"], args["balance"])
    with open(args["output"], "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Interest", args["interest"]])
        writer.writerow(["Payments", months])
        writer.writerow(["Amount", args["balance"]])
        writer.writerow(
            ["Date", "Period", "Payment", "Interest", "Principal", "Balance"]
        )
        for row in amortization_schedule(months, args):
            writer.writerow(row)


if __name__ == "__main__":
    main()


# pmt*(1 + rate*when)/rate*((1 + rate)**nper - 1) == 0
# pv*(1 + rate)**nper +
