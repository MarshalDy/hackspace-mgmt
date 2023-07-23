import enum
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.functions import coalesce, concat
from sqlalchemy import cast
from typing import Optional, List
from datetime import date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class InductionState(enum.Enum):
    valid = "valid"
    expired =  "expired"
    banned =  "banned"

    def __str__(self):
        return f'{self.name}'

class DiscourseInvite(enum.Enum):
    no = "no"
    invited = "invited"
    expired = "expired"
    accepted = "accepted"

    def __str__(self):
        return f'{self.name}'

class Member(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=True)
    preferred_name: Mapped[str] = mapped_column(String(160), nullable=True)

    discourse: Mapped[DiscourseInvite] = mapped_column(nullable=False)
    newsletter: Mapped[bool] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(String(300), nullable=True)
    alt_email: Mapped[str] = mapped_column(String(300), nullable=True)
    payment_ref: Mapped[str] = mapped_column(String(200), nullable=True)
    payment_active: Mapped[bool] = mapped_column(nullable=False)
    join_date: Mapped[date] = mapped_column(nullable=False, default=date.today)
    end_date: Mapped[date] = mapped_column(nullable=True)
    end_reason: Mapped[str] = mapped_column(String(500), nullable=True)
    address1: Mapped[str] = mapped_column(String(200), nullable=True)
    address2: Mapped[str] = mapped_column(String(200), nullable=True)
    town_city: Mapped[str] = mapped_column(String(200), nullable=True)
    county: Mapped[str] = mapped_column(String(200), nullable=True)
    postcode: Mapped[str] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(String(), nullable=True)

    discourse_id: Mapped[Optional[int]] = mapped_column(unique=True)

    cards: Mapped[List["Card"]] = relationship(back_populates="member")
    inductions: Mapped[List["Induction"]] = relationship(back_populates="member", foreign_keys="Induction.member_id")

    @hybrid_property
    def display_name(self):
        if self.preferred_name:
            return self.preferred_name
        else:
            last_name = self.last_name or ""
            return f"{self.first_name} {last_name}".strip()

    @display_name.expression
    def display_name(cls):
        return coalesce(cls.preferred_name, concat(cast(cls.first_name, db.String), cls.last_name))

    def __str__(self):
        return self.display_name

class Card(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    card_serial: Mapped[int] = mapped_column(unique=True, nullable=True)
    number_on_front: Mapped[int] = mapped_column(unique=True, nullable=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=True)
    member: Mapped["Member"] = relationship(back_populates="cards")

    def __str__(self):
        return f"#{self.number_on_front}"

class Machine(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    controllers: Mapped[List["MachineController"]] = relationship(back_populates="machine")
    inductions: Mapped[List["Induction"]] = relationship(back_populates="machine")

    def __str__(self):
        return self.name

class MachineController(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mac: Mapped[int] = mapped_column(unique=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machine.id"))
    machine: Mapped["Machine"] = relationship(back_populates="controllers")
    requires_update: Mapped[bool] = mapped_column()

    def __str__(self):
        return hex(self.mac)

class Induction(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"))
    machine_id: Mapped[int] = mapped_column(ForeignKey("machine.id"))
    state: Mapped[InductionState] = mapped_column(nullable=False)
    inducted_by: Mapped[int] = mapped_column(ForeignKey("member.id"))
    inducted_on: Mapped[date] = mapped_column(nullable=False, default=date.today)

    member: Mapped["Member"] = relationship(back_populates="inductions", foreign_keys=[member_id])
    inductor: Mapped["Member"] = relationship(foreign_keys=[inducted_by])
    machine: Mapped["Machine"] = relationship(back_populates="inductions")
