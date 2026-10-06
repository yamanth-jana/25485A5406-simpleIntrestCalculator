from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)


@app.route('/')
def index():
    return send_file(Path(__file__).with_name('index.html'))


@app.route('/home/<path:name>')
def home(name):
    return f'Hi {name}, welcome!'


@app.route('/delete/<int:id>')
def delete(id):
    return f'Item deleted: {id}'


@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    if request.method == 'GET':
        return jsonify({
            'message': 'Submit loan details using POST to calculate a simple-interest estimate.',
            'required_fields': ['principal', 'annual_rate', 'term_months', 'start_date'],
        })

    payload = request.get_json(silent=True) if request.is_json else request.form
    if not payload:
        return jsonify({'error': 'Submit the loan details as JSON or form data.'}), 400

    try:
        principal = Decimal(str(payload.get('principal', '')))
        annual_rate = Decimal(str(payload.get('annual_rate', '')))
        term_value = Decimal(str(payload.get('term_months', '')))
    except (InvalidOperation, ValueError):
        return jsonify({'error': 'Enter valid numbers for amount, rate, and term.'}), 400

    if not principal.is_finite() or principal <= 0 or principal > Decimal('1000000000000'):
        return jsonify({'error': 'Loan amount must be greater than 0 and no more than 1,000,000,000,000.'}), 400
    if not annual_rate.is_finite() or annual_rate < 0 or annual_rate > 1000:
        return jsonify({'error': 'Annual interest rate must be between 0 and 1,000 percent.'}), 400
    if not term_value.is_finite() or term_value != term_value.to_integral_value():
        return jsonify({'error': 'Loan term must be a whole number of months.'}), 400

    term_months = int(term_value)
    if not 1 <= term_months <= 1200:
        return jsonify({'error': 'Loan term must be between 1 and 1,200 months.'}), 400

    try:
        start_date = date.fromisoformat(str(payload.get('start_date', '')))
    except ValueError:
        return jsonify({'error': 'Choose a valid loan start date.'}), 400

    principal = principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    interest = (
        principal * annual_rate / Decimal('100') * Decimal(term_months) / Decimal('12')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_repayment = principal + interest
    monthly_payment = (total_repayment / term_months).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    closing_year, month_offset = divmod(start_date.month - 1 + term_months, 12)
    closing_year += start_date.year
    closing_month = month_offset + 1
    closing_day = min(start_date.day, monthrange(closing_year, closing_month)[1])
    payoff_date = date(closing_year, closing_month, closing_day)

    return jsonify({
        'principal': format(principal, '.2f'),
        'annual_rate': format(annual_rate, 'f'),
        'term_months': term_months,
        'interest': format(interest, '.2f'),
        'total_repayment': format(total_repayment, '.2f'),
        'monthly_payment': format(monthly_payment, '.2f'),
        'payoff_date': payoff_date.isoformat(),
    })


if __name__ == '__main__':
    app.run(debug=True)