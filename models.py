from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum


db = SQLAlchemy()


# =========================
# Enums
# =========================

class CommunicationType(enum.Enum):
    sms = "sms"
    whatsapp = "whatsapp"
    both = "both"


class OpportunityType(enum.Enum):
    scholarship = "scholarship"
    internship = "internship"
    fellowship = "fellowship"


class StudentGender(enum.Enum):
    M = "M"
    F = "F"


class RecruitmentType(enum.Enum):
    nation_wide_exam = "nation_wide_exam"
    competition = "competition"
    essay_writing = "essay_writing"


class OrgType(enum.Enum):
    ong = "ong"
    company = "company"
    club = "club"
    university = "university"
    association = "association"
    school = "school"


# =========================
# Association Tables
# =========================

student_fields_of_interest = db.Table(
    "student_fields_of_interest",
    db.Column("student_id", db.Integer, db.ForeignKey("student.id"), primary_key=True),
    db.Column("field_id", db.Integer, db.ForeignKey("field.id"), primary_key=True),
)

student_partner = db.Table(
    "student_partner",
    db.Column("student_id", db.Integer, db.ForeignKey("student.id"), primary_key=True),
    db.Column("partner_id", db.Integer, db.ForeignKey("partner.id"), primary_key=True),
)

opportunity_country = db.Table(
    "opportunity_country",
    db.Column("opportunity_id", db.Integer, db.ForeignKey("opportunity.id"), primary_key=True),
    db.Column("country_id", db.Integer, db.ForeignKey("country.id"), primary_key=True),
)

opportunity_field = db.Table(
    "opportunity_field",
    db.Column("opportunity_id", db.Integer, db.ForeignKey("opportunity.id"), primary_key=True),
    db.Column("field_id", db.Integer, db.ForeignKey("field.id"), primary_key=True),
)


# =========================
# Association Model
# =========================
# Kept as a real model because it has extra data: tracked

class StudentOpportunity(db.Model):
    __tablename__ = "student_opportunity"

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunity.id"), primary_key=True)
    tracked = db.Column(db.Boolean, default=False, nullable=False)

    student = db.relationship("Student", back_populates="student_opportunities")
    opportunity = db.relationship("Opportunity", back_populates="student_opportunities")


# =========================
# Core Tables
# =========================

class Language(db.Model):
    __tablename__ = "language"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    students = db.relationship("Student", back_populates="language")

    def __repr__(self):
        return f"<Language {self.name}>"


class Country(db.Model):
    __tablename__ = "country"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    code = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    students = db.relationship("Student", back_populates="country")

    opportunities = db.relationship(
        "Opportunity",
        secondary=opportunity_country,
        back_populates="countries",
    )

    def __repr__(self):
        return f"<Country {self.name}>"


class Field(db.Model):
    __tablename__ = "field"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    students = db.relationship(
        "Student",
        secondary=student_fields_of_interest,
        back_populates="fields_of_interest",
    )

    opportunities = db.relationship(
        "Opportunity",
        secondary=opportunity_field,
        back_populates="fields",
    )

    def __repr__(self):
        return f"<Field {self.name}>"


class Partner(db.Model):
    __tablename__ = "partner"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(OrgType), nullable=False)

    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id"), nullable=True)

    phone_number_1 = db.Column(db.String(30), nullable=True)
    phone_number_1_code = db.Column(db.String(10), nullable=True)
    phone_number_2 = db.Column(db.String(30), nullable=True)
    phone_number_2_code = db.Column(db.String(10), nullable=True)

    email = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(500), nullable=True)
    logo = db.Column(db.String(500), nullable=True)

    recruitment_type = db.Column(db.Enum(RecruitmentType), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    country = db.relationship("Country")
    students = db.relationship(
        "Student",
        secondary=student_partner,
        back_populates="partners",
    )

    def __repr__(self):
        return f"<Partner {self.name}>"


class Opportunity(db.Model):
    __tablename__ = "opportunity"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(OpportunityType), nullable=False)

    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)

    email = db.Column(db.String(255), nullable=True)
    phone_number_1 = db.Column(db.String(30), nullable=True)
    phone_number_1_code = db.Column(db.String(10), nullable=True)
    phone_number_2 = db.Column(db.String(30), nullable=True)
    phone_number_2_code = db.Column(db.String(10), nullable=True)

    offering_entity = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.Enum(StudentGender), nullable=True)
    available = db.Column(db.Boolean, default=True, nullable=False)
    opportunity_location = db.Column(db.String(255), nullable=True)

    image = db.Column(db.String(500), nullable=True)
    link = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    countries = db.relationship(
        "Country",
        secondary=opportunity_country,
        back_populates="opportunities",
    )

    fields = db.relationship(
        "Field",
        secondary=opportunity_field,
        back_populates="opportunities",
    )

    student_opportunities = db.relationship(
        "StudentOpportunity",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    students = db.relationship(
        "Student",
        secondary="student_opportunity",
        viewonly=True,
        back_populates="opportunities",
    )

    def __repr__(self):
        return f"<Opportunity {self.name}>"


class Student(UserMixin, db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, unique=True, nullable=True)

    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.Enum(StudentGender), nullable=True)

    email = db.Column(db.String(255), unique=True, nullable=True)

    phone_number = db.Column(db.String(30), nullable=True)
    phone_number_code = db.Column(db.String(10), nullable=True)
    whatsapp_number = db.Column(db.String(30), nullable=True)
    whatsapp_number_code = db.Column(db.String(10), nullable=True)

    institution_name = db.Column(db.String(255), nullable=True)
    level = db.Column(db.String(120), nullable=True)

    country_id = db.Column(db.Integer, db.ForeignKey("country.id"), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(120), nullable=True)

    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=True)
    year_of_graduation = db.Column(db.Integer, nullable=True)

    receive_notification_updates = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)

    communication_mean = db.Column(db.Enum(CommunicationType), nullable=True)

    password_hash = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    country = db.relationship("Country", back_populates="students")
    language = db.relationship("Language", back_populates="students")

    fields_of_interest = db.relationship(
        "Field",
        secondary=student_fields_of_interest,
        back_populates="students",
    )

    partners = db.relationship(
        "Partner",
        secondary=student_partner,
        back_populates="students",
    )

    student_opportunities = db.relationship(
        "StudentOpportunity",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    opportunities = db.relationship(
        "Opportunity",
        secondary="student_opportunity",
        viewonly=True,
        back_populates="students",
    )

    pathway_results = db.relationship(
        "PathwayResult",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self):
        return bool(self.status)

    def __repr__(self):
        return f"<Student {self.first_name} {self.last_name}>"


class Tip(db.Model):
    __tablename__ = "tip"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<Tip {self.id}>"


class PathwayResult(db.Model):
    __tablename__ = "pathway_result"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    selected_subjects_json = db.Column(db.Text, nullable=False)
    results_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="pathway_results")
