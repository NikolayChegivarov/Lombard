

def price_calculator(main_proba, decimals=2):
    """Функция для подсчета остальных проб."""
    proba_375 = round(main_proba * 375 / 585, decimals)
    proba_500 = round(main_proba * 500 / 585, decimals)
    proba_585 = main_proba
    proba_750 = round(main_proba * 750 / 585, decimals)
    proba_850 = round(main_proba * 850 / 585, decimals)

    result = {
        "proba_375": proba_375,
        "proba_500": proba_500,
        "proba_585": proba_585,
        "proba_750": proba_750,
        "proba_850": proba_850
    }

    return result
