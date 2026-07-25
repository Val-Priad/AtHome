from uuid import UUID

from sqlalchemy import Select, and_, false, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from domain.estate.enums.estate_listing_enums import ListingStatus
from domain.estate.estate_filter_config import (
    DIRECT_FILTERS,
    RELATION_FILTERS,
    SORT_CONFIG,
)
from domain.estate.estate_model import Estate
from domain.estate.models.estate_listing_model import EstateListing
from domain.estate.models.estate_vicinity_model import EstateVicinity
from domain.estate.models.saved_estate_model import SavedEstate
from exceptions.custom_exceptions.estate_exceptions import EstateNotFoundError
from schemas.estate_schemas.requests.estate_filter_request import (
    EstateAdminFilterRequest,
    EstatePublicFilterRequest,
    SortOrder,
)


class EstateRepository:
    def estate_exists(self, session: Session, estate_id: UUID) -> bool:
        return session.get(Estate, estate_id) is not None

    def add(self, session: Session, estate: Estate) -> Estate:
        session.add(estate)
        session.flush()
        return estate

    def get_full_estate_by_id(
        self,
        session: Session,
        estate_id: UUID,
    ) -> Estate:
        stmt = (
            select(Estate)
            .where(Estate.id == estate_id)
            .options(*self._full_load_options())
        )

        estate = session.scalar(stmt)

        if estate is None:
            raise EstateNotFoundError()

        return estate

    def get_full_estate_by_id_for_update(
        self,
        session: Session,
        estate_id: UUID,
    ) -> Estate:
        stmt = (
            select(Estate)
            .where(Estate.id == estate_id)
            .options(*self._full_load_options())
            .with_for_update(of=Estate)
        )
        estate = session.scalar(stmt)
        if estate is None:
            raise EstateNotFoundError()
        return estate

    def delete_estate_by_id(
        self,
        session: Session,
        estate_id: UUID,
    ) -> None:
        estate = session.get(Estate, estate_id)
        if estate is None:
            raise EstateNotFoundError()

        session.delete(estate)

    def get_public_estates_by_filters(
        self,
        session: Session,
        filters: EstatePublicFilterRequest,
        requester_id: UUID | None = None,
    ) -> tuple[list[Estate], int]:
        stmt = select(Estate)

        stmt = stmt.where(
            Estate.listing.has(EstateListing.status == ListingStatus.active)
        )

        stmt = self._apply_filters(
            stmt=stmt,
            filters=filters,
            requester_id=requester_id,
            is_admin=False,
        )

        total = self._count(session, stmt)

        stmt = (
            self._apply_sorting(stmt, filters)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .options(*self._list_load_options())
        )

        estates = list(session.scalars(stmt).unique())

        return estates, total

    def get_admin_estates_by_filters(
        self,
        session: Session,
        filters: EstateAdminFilterRequest,
        requester_id: UUID | None = None,
    ) -> tuple[list[Estate], int]:
        stmt = select(Estate)

        stmt = self._apply_filters(
            stmt=stmt,
            filters=filters,
            requester_id=requester_id,
            is_admin=True,
        )

        total = self._count(session, stmt)

        stmt = (
            self._apply_sorting(stmt, filters)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .options(*self._list_load_options())
        )

        estates = list(session.scalars(stmt).unique())

        return estates, total

    def toggle_saved(
        self,
        session: Session,
        requester_id: UUID,
        estate_id: UUID,
    ) -> None:
        record = self._get_saved_estate_or_none(
            session, requester_id, estate_id
        )
        if record:
            session.delete(record)
        else:
            session.add(SavedEstate(user_id=requester_id, estate_id=estate_id))

    def _get_saved_estate_or_none(
        self, session: Session, requester_id: UUID, estate_id: UUID
    ) -> SavedEstate | None:
        return session.execute(
            select(SavedEstate).where(
                and_(
                    SavedEstate.user_id == requester_id,
                    SavedEstate.estate_id == estate_id,
                )
            )
        ).scalar_one_or_none()

    def _apply_filters(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
        requester_id: UUID | None,
        is_admin: bool,
    ) -> Select:
        stmt = self._apply_direct_filters(stmt, filters)
        stmt = self._apply_admin_filters(stmt, filters, is_admin)
        stmt = self._apply_saved_filter(stmt, filters, requester_id)
        stmt = self._apply_relation_filters(stmt, filters)
        stmt = self._apply_vicinity_filters(stmt, filters)

        return stmt

    def _apply_direct_filters(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
    ) -> Select:
        for filter_type, column, *fields in DIRECT_FILTERS:
            if filter_type == "eq":
                stmt = self._eq(stmt, column, getattr(filters, fields[0]))

            elif filter_type == "in":
                stmt = self._in(stmt, column, getattr(filters, fields[0]))

            elif filter_type == "range":
                stmt = self._range(
                    stmt,
                    column,
                    getattr(filters, fields[0]),
                    getattr(filters, fields[1]),
                )

            else:
                raise ValueError(f"Unknown direct filter type: {filter_type}")

        return stmt

    def _apply_admin_filters(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
        is_admin: bool,
    ) -> Select:
        if not is_admin or not isinstance(filters, EstateAdminFilterRequest):
            return stmt

        stmt = self._eq(stmt, Estate.seller_id, filters.seller_id)
        stmt = self._has_in(
            stmt,
            Estate.listing,
            EstateListing.status,
            filters.status,
        )

        return stmt

    def _apply_saved_filter(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
        requester_id: UUID | None,
    ) -> Select:
        if filters.saved_by_current_user is None:
            return stmt

        if requester_id is None:
            if filters.saved_by_current_user is True:
                return stmt.where(false())

            return stmt

        exists_saved = (
            select(1)
            .where(
                SavedEstate.estate_id == Estate.id,
                SavedEstate.user_id == requester_id,
            )
            .exists()
        )

        if filters.saved_by_current_user is True:
            return stmt.where(exists_saved)

        return stmt.where(~exists_saved)

    def _apply_relation_filters(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
    ) -> Select:
        for filter_type, relationship, column, *fields in RELATION_FILTERS:
            if filter_type == "eq":
                stmt = self._has_eq(
                    stmt,
                    relationship,
                    column,
                    getattr(filters, fields[0]),
                )

            elif filter_type == "in":
                stmt = self._has_in(
                    stmt,
                    relationship,
                    column,
                    getattr(filters, fields[0]),
                )

            elif filter_type == "range":
                stmt = self._has_range(
                    stmt,
                    relationship,
                    column,
                    getattr(filters, fields[0]),
                    getattr(filters, fields[1]),
                )

            elif filter_type == "presence":
                stmt = self._has_presence(
                    stmt,
                    relationship,
                    column,
                    getattr(filters, fields[0]),
                )

            else:
                raise ValueError(
                    f"Unknown relation filter type: {filter_type}"
                )

        return stmt

    def _apply_vicinity_filters(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
    ) -> Select:
        if filters.vicinity_type:
            for vicinity_type in filters.vicinity_type:
                conditions = [EstateVicinity.type == vicinity_type]

                if filters.vicinity_distance_m_to is not None:
                    conditions.append(
                        EstateVicinity.distance_m
                        <= filters.vicinity_distance_m_to
                    )

                stmt = stmt.where(Estate.vicinities.any(and_(*conditions)))

            return stmt

        if filters.vicinity_distance_m_to is not None:
            stmt = stmt.where(
                Estate.vicinities.any(
                    EstateVicinity.distance_m <= filters.vicinity_distance_m_to
                )
            )

        return stmt

    def _apply_sorting(
        self,
        stmt: Select,
        filters: EstatePublicFilterRequest | EstateAdminFilterRequest,
    ) -> Select:
        sort_column, relationship = SORT_CONFIG[filters.sort_by]

        if relationship is not None:
            stmt = stmt.outerjoin(relationship)

        order_expr = (
            sort_column.asc().nulls_last()
            if filters.order == SortOrder.asc
            else sort_column.desc().nulls_last()
        )

        return stmt.order_by(order_expr, Estate.id.asc())

    def _count(self, session: Session, stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).subquery()
        )

        return session.scalar(count_stmt) or 0

    def _eq(self, stmt: Select, column, value) -> Select:
        if value is None:
            return stmt

        return stmt.where(column == value)

    def _in(self, stmt: Select, column, values) -> Select:
        if values is None or len(values) == 0:
            return stmt

        return stmt.where(column.in_(values))

    def _range(self, stmt: Select, column, value_from, value_to) -> Select:
        if value_from is not None:
            stmt = stmt.where(column >= value_from)

        if value_to is not None:
            stmt = stmt.where(column <= value_to)

        return stmt

    def _has_eq(self, stmt: Select, relationship, column, value) -> Select:
        if value is None:
            return stmt

        return stmt.where(relationship.has(column == value))

    def _has_in(self, stmt: Select, relationship, column, values) -> Select:
        if values is None or len(values) == 0:
            return stmt

        return stmt.where(relationship.has(column.in_(values)))

    def _has_range(
        self,
        stmt: Select,
        relationship,
        column,
        value_from,
        value_to,
    ) -> Select:
        conditions = []

        if value_from is not None:
            conditions.append(column >= value_from)

        if value_to is not None:
            conditions.append(column <= value_to)

        if not conditions:
            return stmt

        return stmt.where(relationship.has(and_(*conditions)))

    def _has_presence(
        self,
        stmt: Select,
        relationship,
        column,
        value: bool | None,
    ) -> Select:
        if value is None:
            return stmt

        if value is True:
            return stmt.where(relationship.has(column.is_not(None)))

        return stmt.where(relationship.has(column.is_(None)))

    def _list_load_options(self):
        return (
            joinedload(Estate.location),
            joinedload(Estate.pricing),
            joinedload(Estate.listing),
            joinedload(Estate.details),
            joinedload(Estate.apartment),
            joinedload(Estate.house),
            selectinload(Estate.media),
        )

    def _full_load_options(self):
        return (
            joinedload(Estate.seller),
            joinedload(Estate.agent),
            joinedload(Estate.location),
            joinedload(Estate.pricing),
            joinedload(Estate.listing),
            joinedload(Estate.utilities),
            joinedload(Estate.details),
            joinedload(Estate.apartment),
            joinedload(Estate.house),
            selectinload(Estate.translations),
            selectinload(Estate.media),
            selectinload(Estate.vicinities),
        )
