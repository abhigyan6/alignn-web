from alembic import context

from alignn.audit import AuditRecord  # noqa: F401
from alignn.db import Base, engine
from alignn.domains.applications import models as application_models  # noqa: F401
from alignn.domains.files import models as file_models  # noqa: F401
from alignn.domains.identity import models  # noqa: F401
from alignn.domains.opportunities import models as opportunity_models  # noqa: F401
from alignn.domains.organizations import models as organization_models  # noqa: F401
from alignn.domains.profiles import models as profiles_models  # noqa: F401
from alignn.jobs import models as jobs_models  # noqa: F401

config = context.config
target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=str(engine.url), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
