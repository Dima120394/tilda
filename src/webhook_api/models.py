import sqlalchemy as sa

from .ext import db

__all__ = (
    'OrderEntryState',
    'Order',
    'OrderEntry',
)
import dataclasses
import enum


@dataclasses.dataclass()
class OrderRequestDetails:
    email: str
    order_id: str
    systran_id: str
    orders_amount: int


class OrderEntryState(enum.Enum):
    created = 1  # Initial state; Order entry created
    rejected = 2  # Order rejected
    fulfilled = 3  # API invocation successfull
    not_payed = 4  # total price < calculated price
    failed = 5
    dummy = 6


class Providers(enum.Enum):
    dummy = 0
    socproof = 1
    justanotherpanel = 2
    prosmmstore = 3
    fxsmmsoc = 4


@dataclasses.dataclass()
class ServiceProvider:
    service_name: str
    service_id: str
    provider_id: str


class RequestLogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String, comment='Request Content-Type')
    raw_data = db.Column(db.Text, comment='Raw data from Tilda')
    created_at = db.Column(db.DateTime(timezone=True), server_default=sa.func.now())


class ServiceDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String, unique=True, comment='Service name')
    service_id = db.Column(db.String, comment='Provider sevice ID')
    provider_id = db.Column(db.Enum(Providers), comment='Provider entry')

    def __repr__(self) -> str:
        return f'<Service name={self.service_name} id={self.provider_id.name}:{self.service_id}>'

    @classmethod
    def get_index(cls):
        _index = {}
        results = db.session.execute(
            db.select(cls)
        ).all()
        for [entry] in results:
            _index[str(entry.service_name).lower()] = entry
        return _index


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String, unique=True, comment='Tilda\s order ID')
    email = db.Column(db.String, unique=False, comment='Associated email')
    systran_id = db.Column(db.String, unique=False, comment='Tilda\s transaction ID')
    payment_system = db.Column(db.String, comment='Payment systemd ID')
    raw_data = db.Column(db.Text, comment='Raw data from Tilda')
    orders_amount = db.Column(db.Integer)
    orders = db.relationship('OrderEntry', backref='order')
    created_at = db.Column(db.DateTime(timezone=True), server_default=sa.func.now())

    def __repr__(self) -> str:
        return f'<Order id={self.order_id} products={self.orders_amount}>'


class OrderEntry(db.Model):
    __tablename__ = 'order_entries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, comment='Payment systemd ID')
    entry_id = db.Column(db.String, unique=True)
    state = db.Column(db.Enum(OrderEntryState))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False,
                         comment='Parent order')
    created_at = db.Column(db.DateTime(timezone=True), server_default=sa.func.now())

    # parsed data
    service_name = db.Column(db.String, comment='Service name; Resolved to provider service id later')
    price_per_unit = db.Column(db.Float)
    per_unit = db.Column(db.Integer)
    url = db.Column(db.Text, comment='Target url')
    units_amount = db.Column(db.Float)
    quantity = db.Column(db.Float)
    amount = db.Column(db.Float)
    price = db.Column(db.Float)

    is_payed = db.Column(db.Boolean, comment='Is order payed (price_total >= calculated)')
    is_package = db.Column(db.Boolean, comment='Is order entry parsed as "Package"')
    provider_id = db.Column(db.Enum(Providers))
    service_id = db.Column(db.String, comment='Resolved service id')
    provider_order_id = db.Column(db.String, comment='OrderID from service provider')
    error_hint = db.Column(db.String, comment='Error message from provider')
    # service related

    def __repr__(self) -> str:
        return f'<OrderEntry state={self.state} id={self.entry_id} name={self.service_name}>'
