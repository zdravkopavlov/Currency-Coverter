# calculator.py

EXCHANGE_RATE = 1.95583

def bgn_to_eur(bgn):
    """Convert BGN to EUR, rounded to 2 decimals."""
    return round(float(bgn) / EXCHANGE_RATE, 2)

def eur_to_bgn(eur):
    """Convert EUR to BGN, rounded to 2 decimals."""
    return round(float(eur) * EXCHANGE_RATE, 2)

def calculate_change(price_bgn, paid_bgn):
    """
    Given a price in BGN and paid amount in BGN,
    return change in EUR (rounded to 2 decimals).
    """
    change_bgn = float(paid_bgn) - float(price_bgn)
    return bgn_to_eur(change_bgn) if change_bgn >= 0 else 0.0
