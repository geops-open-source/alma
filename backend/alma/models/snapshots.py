"""
Implementation of db-level snapshots

Builds on the [Versioning using Temporal Rows][1] examples from the SQLAlchemy
documentation, specifically [versioned_rows][2]. The main takeaway is the use of
`make_transient` (combined with clearing the primary key) to cause a loaded
object to be re-inserted as a new row on the next flush.

The main difference between our version and the example is that instead of
updating dependent objects to point to the new current version, as shown in the
second part of the example, we recursively also make all dependent objects
transient, causing them to be re-inserted as well.

[1]: https://docs.sqlalchemy.org/en/20/orm/examples.html#module-examples.versioned_rows
[2]: https://docs.sqlalchemy.org/en/20/_modules/examples/versioned_rows/versioned_rows.html
"""

from dataclasses import field
from enum import Enum, auto

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    RelationshipDirection,
    Session,
    make_transient,
    mapped_column,
    validates,
)
from sqlalchemy.orm.attributes import flag_dirty, instance_state


class HistorizationError(Exception):
    pass


class ImmutableInstanceError(HistorizationError):
    """
    Raised when modification of an immutable snapshot is attempted.
    """


class SnapshotType(Enum):
    MUTABLE = auto()
    IMMUTABLE = auto()


class SupportsSnapshots(MappedAsDataclass, kw_only=True):
    """
    Mixin for all objects which can be snapshotted as part of historization.
    """

    is_current: Mapped[bool] = mapped_column(init=False, insert_default=True)
    _snapshot_type: SnapshotType | None = field(init=False, repr=False, default=None)

    @validates("is_current")
    def validate_is_current(self, name: str, value: object):
        raise AttributeError(f"Attribute {type(self).__name__}.{name} is read-only")

    @property
    def _should_create_snapshot(self) -> bool:
        return self._snapshot_type is not None

    def _create_immutable_snapshot(self) -> None:
        self._create_snapshot(SnapshotType.IMMUTABLE)

    def _create_mutable_snapshot(self) -> None:
        self._create_snapshot(SnapshotType.MUTABLE)

    def _create_snapshot(self, snapshot_type: SnapshotType) -> None:
        """
        Create a new snapshot of this object and all dependent objects.
        """
        session = Session.object_session(self)
        assert session

        # Make sure all pending changes that have not been flushed yet are
        # rolled into the snapshot.
        session.flush()

        # Set flag to create snapshot on the next flush.
        self._snapshot_type = snapshot_type

        # Explicitly mark the instance as dirty so it takes part in the
        # "before_flush" event even if its data has not changed.
        flag_dirty(self)

        # Flush to trigger snapshotting.
        session.flush()

    def _make_transient(self, snapshot_type: SnapshotType) -> None:
        """
        Mark the object and all dependent objects as transient.
        """
        cls = type(self)
        mapper = sa.inspect(cls)
        assert mapper
        # Recursively call `_make_transient()` on any related object, where the
        # related object has a foreign key pointing to the current object.
        # This could be a one-to-many or one-to-one relation.
        for rel_name, rel in mapper.relationships.items():
            # Only consider relationships where the foreign key points to us that are not
            # marked as 'viewonly' (because they are based on a custom join and not writeable).
            if rel.direction is not RelationshipDirection.ONETOMANY or rel.viewonly:
                continue
            if not issubclass(rel.entity.class_, SupportsSnapshots):
                raise HistorizationError(
                    f"Type of {cls.__name__}.{rel_name} does not support historization: {rel.entity.class_}"
                )
            if rel.uselist:  # one to many
                for related_model in getattr(self, rel_name):
                    related_model._make_transient(snapshot_type)
            else:  # one to one
                related_model = getattr(self, rel_name)
                if related_model is not None:
                    related_model._make_transient(snapshot_type)

        [pk_column] = mapper.primary_key
        pk_property = mapper.get_property_by_column(pk_column)
        pk_value = getattr(self, pk_property.key)

        if snapshot_type is SnapshotType.IMMUTABLE:
            session = Session.object_session(self)
            assert session

            # Use a non-ORM enabled query to update 'is_current' of the
            # snapshot in the database.
            query = sa.update(cls).where(pk_property.expression == pk_value)
            session.connection().execute(query, {"is_current": False})

        # Make this object transient and reset the primary key. This will cause an
        # INSERT to be emitted instead of an UPDATE on the next flush.
        make_transient(self)
        setattr(self, pk_property.key, None)

    @staticmethod
    def handle_historization(
        session: Session, flush_context: object, instances: object
    ) -> None:
        """
        SQLAlchemy "before_flush" hook.

        Creates snapshots when requested and enforces snapshot immutability.
        """
        for instance in session.dirty:
            if not isinstance(instance, SupportsSnapshots):
                continue
            if not instance_state(instance).has_identity:
                # Skip objects that have only been added to the session but not persisted yet
                # (no "identity" = no primary key).
                continue
            if not instance.is_current:
                raise ImmutableInstanceError(
                    f"Trying to modify immutable snapshot: {instance}"
                )

            if instance._snapshot_type:
                instance._make_transient(instance._snapshot_type)
                instance._snapshot_type = None  # Reset flag
                session.add(instance)


# Set up event handler for historization
sa.event.listen(Session, "before_flush", SupportsSnapshots.handle_historization)  # type: ignore
