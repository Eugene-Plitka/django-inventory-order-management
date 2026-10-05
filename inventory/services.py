from django.db import transaction

from .models import Stock, StockMovement


class StockServiceError(Exception):
    pass


class InvalidStockAdjustment(StockServiceError):
    pass


@transaction.atomic
def adjust_stock(*, stock_id, quantity, reason, performed_by):
    if quantity == 0:
        raise InvalidStockAdjustment("Adjustment quantity cannot be zero.")

    if not reason.strip():
        raise InvalidStockAdjustment("Adjustment reason is required.")

    stock = Stock.objects.select_for_update().get(pk=stock_id)

    new_quantity = stock.quantity + quantity

    if new_quantity < 0:
        raise InvalidStockAdjustment("Stock quantity cannot become negative.")

    stock.quantity = new_quantity
    stock.save(
        update_fields=(
            "quantity",
            "updated_at",
        )
    )

    movement_type = (
        StockMovement.MovementType.ADJUSTMENT_IN
        if quantity > 0
        else StockMovement.MovementType.ADJUSTMENT_OUT
    )

    StockMovement.objects.create(
        stock=stock,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        performed_by=performed_by,
    )

    return stock
