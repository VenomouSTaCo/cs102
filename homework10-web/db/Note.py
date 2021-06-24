from typing import Tuple, List

from sqlalchemy import String, Integer, select, ForeignKey, and_
from sqlalchemy import Column

from db.engine_generator import Base


class Note(Base):  # type:ignore
    __tablename__ = "Notes"
    id = Column(Integer, primary_key=True)
    title = Column("title", String(50))
    text = Column("text", String(1 << 16))
    user_id = Column("user_id", Integer, ForeignKey("Users.id"))

    @staticmethod
    def create_note(title: str, text: str, user_id, session_builder) -> Tuple[int, str, str]:
        with session_builder() as session:
            note = Note(title=title, text=text, user_id=user_id)
            session.add(note)
            session.commit()

            return note.id, note.title, note.text

    @staticmethod
    def get_by_user_id(user_id, session_builder) -> List[Tuple[int, str, str]]:
        with session_builder() as session:
            notes = session.execute(select(Note).where(Note.user_id == user_id)).fetchall()
            result = []
            if notes:
                for note in notes:
                    result.append((note.Note.id, note.Note.title, note.Note.text))
            return result

    @staticmethod
    def edit(id: int, title: str, text: str, user_id: int, session_builder) -> Tuple[int, str, str]:
        with session_builder() as session:

            note = (
                session.execute(select(Note).where(and_(Note.id == id, Note.user_id == user_id)))
                .fetchall()[0]
                .Note
            )
            note.title = title
            note.text = text
            session.commit()

            return note.id, note.title, note.text

    @staticmethod
    def delete(id: int, user_id: int, session_builder):
        with session_builder() as session:
            session.query(Note).filter(and_(Note.id == id, Note.user_id == user_id)).delete()
            session.commit()
