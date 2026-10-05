class SalesOrderServiceError(Exception):
    pass


class InvalidSalesOrderStatus(SalesOrderServiceError):
    pass


class InsufficientStock(SalesOrderServiceError):
    pass
