"""SQLAlchemy ORM 模型"""
from sqlalchemy import Column, Integer, String, Numeric, Index
from database import Base


class FreightRate(Base):
    """承运商费率表"""
    __tablename__ = "freight_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    carrier = Column(String(20), nullable=False, comment="承运商代码")
    orig_port = Column(String(20), nullable=False, comment="起运港代码")
    dest_port = Column(String(20), nullable=False, comment="目的港代码")
    min_weight = Column(Numeric(10, 3), nullable=False, comment="最小重量(kg)")
    max_weight = Column(Numeric(10, 3), nullable=False, comment="最大重量(kg)")
    service_level = Column(String(10), nullable=False, comment="服务级别(DTD/DTP)")
    min_cost = Column(Numeric(10, 2), nullable=False, comment="最低费用($)")
    rate = Column(Numeric(10, 2), nullable=False, comment="单价($/kg)")
    mode = Column(String(10), nullable=False, comment="运输方式(AIR/GROUND)")
    transport_days = Column(Integer, nullable=False, comment="运输天数")
    carrier_type = Column(String(20), nullable=False, comment="承运商类型")
    service_rating = Column(String(1), nullable=False, comment="服务评级(A-E)")

    __table_args__ = (
        Index("idx_orig_dest", "orig_port", "dest_port"),
        Index("idx_carrier", "carrier"),
        Index("idx_weight", "min_weight", "max_weight"),
        Index("idx_port_weight", "orig_port", "dest_port", "min_weight", "max_weight"),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "carrier": self.carrier,
            "orig_port": self.orig_port,
            "dest_port": self.dest_port,
            "min_weight": float(self.min_weight),
            "max_weight": float(self.max_weight),
            "service_level": self.service_level,
            "min_cost": float(round(self.min_cost, 2)),
            "rate": float(round(self.rate, 2)),
            "mode": self.mode,
            "transport_days": self.transport_days,
            "carrier_type": self.carrier_type,
            "service_rating": self.service_rating,
        }
