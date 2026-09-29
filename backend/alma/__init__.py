"""alma package root.

The two imports below are a deliberate, order-sensitive bootstrap step and
must stay exactly in this order at the very top of this file:

1. ``business_workflow_manager.models`` defines wm's ORM classes/Tables (e.g.
   ``wf_node``, ``wf_config``) with no schema qualification.
2. ``alma.workflow_integration`` mutates that already-constructed metadata
   (re-scopes wm's tables to the ``alma`` schema, adds alma-specific ORM
   relationships onto ``wm.Node``, registers alma's event handlers).

Because Python fully executes a package's ``__init__.py`` before running any
of its submodules (``import alma.anything`` always triggers this file first),
placing the bootstrap here - rather than relying on whichever module happens
to import ``workflow_integration`` first - guarantees the mutation always
runs before any code path can query/flush wm models, no matter which part of
the app is imported first (API entry point, CLI, or test suite).

Do not remove or reorder these imports, and do not move this logic to a
lazily-imported submodule.
"""

import business_workflow_manager.models  # noqa: F401  (dummy import, see above)  # pyright: ignore

import alma.workflow_integration  # noqa: F401  (dummy import, see above)  # pyright: ignore
