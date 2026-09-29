import math
from typing import Any

import business_workflow_manager.models as wf_models
from sqlalchemy import (
    Date,
    SQLColumnExpression,
    and_,
    cast,
    desc,
    false,
    func,
    or_,
    select,
    true,
    union,
)
from sqlalchemy.orm import Session, aliased, selectinload

from alma.models import auth

from ..types.workflow import (
    GeschaefteFilter,
    PaginatedTaskResult,
    SortTasks,
    Task,
)


def _build_order_by(
    model: type[wf_models.Node],
    sort_by: SortTasks,
    reverse: bool,
) -> list[SQLColumnExpression[Any]]:
    """Build ORDER BY columns for a Node model/alias with stable tiebreaker."""
    cols: list[SQLColumnExpression[Any]] = []
    match sort_by:
        case SortTasks.StartDatum:
            cols.append(
                desc(cast(model.started_at, Date))
                if reverse
                else cast(model.started_at, Date)
            )
        case SortTasks.Faelligkeit:
            cols.append(desc(model.deadline) if reverse else model.deadline)
    cols.append(desc(model.wf_node_id) if reverse else model.wf_node_id)
    return cols


def get_paginated_task_result(
    session: Session,
    user: auth.User,
    filter_: GeschaefteFilter | None = None,
    page: int = 1,
    per_page: int = 20,
    task_id: int | None = None,
    sort_by: SortTasks = SortTasks.StartDatum,
    reverse: bool = False,
    as_tree: bool = False,
    where_clause: SQLColumnExpression[bool] | None = None,
) -> PaginatedTaskResult:
    """
    Get a page of tasks by page number or a task id that is contained on the page.
    """

    if as_tree:
        condition = wf_models.Node.parent_id == None  # pyright: ignore reportUnnecessaryComparison # noqa
        if where_clause is not None:
            where_clause = and_(where_clause, condition)
        else:
            where_clause = condition

    if where_clause is None:
        where_clause = true()

    # we need these aliases for filtering on child and grandchild nodes
    child_table = aliased(wf_models.Node)
    grandchild_table = aliased(wf_models.Node)

    # If we filter on the tree, we need to ensure that the filter is applied on the children and
    # grandchildren as well. These are only aliases as we need to perform multiple joins later on.
    child_table_filter_clause = (
        filter_.gen_filter_clause(child_table, user)
        if (filter_ and as_tree)
        else true()
    )
    child_query = (
        select(wf_models.Node.wf_node_id)
        .join(child_table, wf_models.Node.wf_node_id == child_table.parent_id)
        .where(child_table_filter_clause, where_clause)
        .distinct()
    )
    grandchild_table_filter_clause = (
        filter_.gen_filter_clause(grandchild_table, user)
        if (filter_ and as_tree)
        else true()
    )
    grandchild_query = (
        select(wf_models.Node.wf_node_id)
        .join(child_table, wf_models.Node.wf_node_id == child_table.parent_id)
        .join(grandchild_table, child_table.wf_node_id == grandchild_table.parent_id)
        .where(grandchild_table_filter_clause, where_clause)
    )
    filter_clause = (
        filter_.gen_filter_clause(wf_models.Node, user) if filter_ else true()
    )
    parent_query = select(wf_models.Node.wf_node_id).where(filter_clause, where_clause)

    all_parents_query = parent_query
    if filter_ and as_tree:
        # the filter must be applied on the children and grandchildren as well if we have a tree.
        # If a grandchild/child is found we need to ensure that top-most node is returned.
        # Therefore, we look for the parents/grandparents of tasks in the task tree and return its
        all_parents_query = union(child_query, grandchild_query, parent_query)

    # This subquery contains all the parents that are either not filtered or have children/grandchildren
    # that are not filtered out.
    all_parents_query_sub = all_parents_query.subquery()
    query = select(wf_models.Node).where(
        wf_models.Node.wf_node_id.in_(select(all_parents_query_sub))
    )
    num_parents = session.execute(
        select(func.count()).select_from(all_parents_query_sub)
    ).scalar_one()

    if as_tree:
        # Count all nodes visible in the tree: parents + matching children +
        # matching grandchildren + intermediate children (parents of matching grandchildren).
        parent_ids_query = select(all_parents_query_sub)

        all_children_ids = (
            select(child_table.wf_node_id)
            .join(wf_models.Node, wf_models.Node.wf_node_id == child_table.parent_id)
            .where(
                child_table.parent_id.in_(parent_ids_query),
                child_table_filter_clause,
            )
        )

        all_grandchildren_ids = (
            select(grandchild_table.wf_node_id)
            .join(child_table, child_table.wf_node_id == grandchild_table.parent_id)
            .join(wf_models.Node, wf_models.Node.wf_node_id == child_table.parent_id)
            .where(
                child_table.parent_id.in_(parent_ids_query),
                grandchild_table_filter_clause,
            )
        )

        all_intermediate_children_ids = (
            select(child_table.wf_node_id)
            .join(
                grandchild_table,
                child_table.wf_node_id == grandchild_table.parent_id,
            )
            .join(wf_models.Node, wf_models.Node.wf_node_id == child_table.parent_id)
            .where(
                child_table.parent_id.in_(parent_ids_query),
                grandchild_table_filter_clause,
            )
        )

        all_tree_nodes = union(
            parent_ids_query,
            all_children_ids,
            all_grandchildren_ids,
            all_intermediate_children_ids,
        )
        all_tree_nodes_sub = all_tree_nodes.subquery()
        num_results_total = session.execute(
            select(func.count()).select_from(all_tree_nodes_sub)
        ).scalar_one()
    else:
        num_results_total = num_parents
    query = query.order_by(*_build_order_by(wf_models.Node, sort_by, reverse))

    task_node = session.scalars(
        select(wf_models.Node).where(
            wf_models.Node.wf_node_id == task_id, filter_clause
        )
    ).one_or_none()
    # Calculate page from task_id: we want the page that contains this node
    if task_id and task_node:
        # Count the number of rows that appear before (and including) the row
        # we're interested in, according to the sort criterira.
        if as_tree:
            while task_node.parent:
                task_node = task_node.parent
        new_child_query = child_query.where(true())
        new_grandchild_query = grandchild_query.where(true())
        new_parent_query = parent_query.where(true())
        match sort_by:
            case SortTasks.StartDatum:
                if reverse:
                    filter_statement = or_(
                        cast(wf_models.Node.started_at, Date)
                        > cast(task_node.started_at, Date),
                        and_(
                            cast(wf_models.Node.started_at, Date)
                            == cast(task_node.started_at, Date),
                            wf_models.Node.wf_node_id >= task_node.wf_node_id,
                        ),
                    )

                else:
                    filter_statement = or_(
                        cast(wf_models.Node.started_at, Date)
                        < cast(task_node.started_at, Date),
                        and_(
                            cast(wf_models.Node.started_at, Date)
                            == cast(task_node.started_at, Date),
                            wf_models.Node.wf_node_id <= task_node.wf_node_id,
                        ),
                    )
                if filter_ and as_tree:
                    new_child_query = new_child_query.where(filter_statement)
                    new_grandchild_query = new_grandchild_query.where(filter_statement)
                new_parent_query = new_parent_query.where(filter_statement)

            case SortTasks.Faelligkeit:
                if reverse:
                    filter_statement = or_(
                        false()
                        if task_node.deadline is None
                        else or_(
                            wf_models.Node.deadline > task_node.deadline,
                            wf_models.Node.deadline.is_(None),
                        ),
                        and_(
                            wf_models.Node.deadline == task_node.deadline,
                            wf_models.Node.wf_node_id >= task_node.wf_node_id,
                        ),
                    )
                else:
                    filter_statement = or_(
                        (wf_models.Node.deadline.is_not(None))
                        if task_node.deadline is None
                        else (wf_models.Node.deadline < task_node.deadline),
                        and_(
                            wf_models.Node.deadline == task_node.deadline,
                            wf_models.Node.wf_node_id <= task_node.wf_node_id,
                        ),
                    )
                if filter_ and as_tree:
                    new_child_query = new_child_query.where(filter_statement)
                    new_grandchild_query = new_grandchild_query.where(filter_statement)
                new_parent_query = new_parent_query.where(filter_statement)
        page_subquery = (
            union(new_child_query, new_grandchild_query, new_parent_query).subquery()
            if (filter_ and as_tree)
            else new_parent_query.subquery()
        )
        page_query = select(func.count()).select_from(page_subquery)

        row_number = session.execute(page_query).scalar_one()
        # In tree mode, the node we're looking for might not be a top-level
        # node, so it is not included in the count (filtered by WHERE clause).
        # If there is no other top-level node before it, the query will return 0
        if row_number == 0:
            row_number = 1
        page = math.ceil(row_number / per_page)
    elif task_id and not task_node:
        # if the task node is filtered out, return first page
        page = 1

    query = query.options(selectinload(wf_models.Node.children))
    query = query.limit(per_page).offset(per_page * (page - 1))
    nodes = {n.wf_node_id: n for n in list(session.scalars(query).unique().all())}
    # In tree mode, include the children of all nodes on the current page
    # (nesting is at most two levels deep).
    if as_tree:
        # Order children/grandchildren by parent position first, then by own
        # sort criteria.  This groups siblings together in the correct order.
        child_order = _build_order_by(child_table, sort_by, reverse)
        grandchild_order = _build_order_by(grandchild_table, sort_by, reverse)

        # Get the children of parent nodes and ensure that filtering is applied.
        children_query = (
            select(child_table)
            .join(wf_models.Node, wf_models.Node.wf_node_id == child_table.parent_id)
            .where(
                child_table.parent_id.in_(nodes.keys()),
                child_table_filter_clause,
            )
            .options(selectinload(child_table.children))
            .order_by(*child_order)
        )
        for child in session.scalars(children_query).unique().all():
            nodes[child.wf_node_id] = child

        # Get grandchildren. Ensure that we also return intermediate children.
        grandchildren_query = (
            select(child_table, grandchild_table)
            .join(child_table, child_table.wf_node_id == grandchild_table.parent_id)
            .join(wf_models.Node, wf_models.Node.wf_node_id == child_table.parent_id)
            .where(
                child_table.parent_id.in_(nodes.keys()), grandchild_table_filter_clause
            )
            .options(
                selectinload(child_table.children),
                selectinload(grandchild_table.children),
            )
            .order_by(*child_order, *grandchild_order)
        )

        for grandchild_row in session.execute(grandchildren_query).unique():
            nodes[grandchild_row[0].wf_node_id] = grandchild_row[0]
            nodes[grandchild_row[1].wf_node_id] = grandchild_row[1]

    if task_node:
        # Assert that selected node is actually on the page we're about to return
        assert any(wf_node_id == task_id for wf_node_id in nodes)

    return PaginatedTaskResult(
        page=page,
        per_page=per_page,
        results=[Task.from_db_node(node) for _, node in nodes.items()],
        num_pages=math.ceil(num_parents / per_page),
        num_results_total=num_results_total,
    )
