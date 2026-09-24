def apply_discount(price: int, discount_percent: int) -> int:
    """Precio final en COP (pesos enteros) tras aplicar el descuento del producto.

    Redondea al peso más cercano. Con 0% devuelve el precio tal cual.
    """
    if not discount_percent:
        return price
    return (price * (100 - discount_percent) + 50) // 100
