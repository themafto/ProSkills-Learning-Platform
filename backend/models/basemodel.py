from sqlalchemy import Column, TIMESTAMP, text

from backend.database import Base


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))

    def to_dict(self) -> dict:
        data = {}
        for column in self.__table__.columns:
            data[column.name] = getattr(self, column.name)
        return data