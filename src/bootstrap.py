"""Application bootstrap helpers for wiring dispatcher dependencies."""

from dataclasses import dataclass, fields
import logging

from aiogram import Dispatcher

from settings import JSON_PATH, settings
from storage import JsonStorage, ensure_json_storage
from telegram.handlers import admin_router, group_router, record_router, system_router
from use_cases import (
    AddGroupUseCase,
    AddRecordUseCase,
    CountRecordsUseCase,
    DeleteGroupUseCase,
    DeleteRecordUseCase,
    EditRecordUseCase,
    GetRecordUseCase,
    GrantAdminUseCase,
    ListAdminsUseCase,
    ListGroupsUseCase,
    ListRecordGroupsUseCase,
    RevokeAdminUseCase,
    ValidateGroupLimitUseCase,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AppDependencies:
    """Container with all dependencies injected into the dispatcher."""

    storage: JsonStorage
    list_groups: ListGroupsUseCase
    validate_group_limit: ValidateGroupLimitUseCase
    add_group: AddGroupUseCase
    delete_group: DeleteGroupUseCase
    list_record_groups: ListRecordGroupsUseCase
    add_record: AddRecordUseCase
    count_records: CountRecordsUseCase
    get_record: GetRecordUseCase
    edit_record: EditRecordUseCase
    delete_record: DeleteRecordUseCase
    grant_admin: GrantAdminUseCase
    list_admins: ListAdminsUseCase
    revoke_admin: RevokeAdminUseCase
    owners: list[int]
    group_limit: int

    def register(self, dispatcher: Dispatcher) -> None:
        """Register all dependencies in the dispatcher workflow data."""

        for field in fields(self):
            dispatcher[field.name] = getattr(self, field.name)
        logger.debug("Dependencies registered in dispatcher keys=%s", [field.name for field in fields(self)])


def build_dependencies() -> AppDependencies:
    """Build all application dependencies from concrete implementations."""

    logger.debug("Building application dependencies storage_path=%s", JSON_PATH)
    storage = JsonStorage(JSON_PATH)
    return AppDependencies(
        storage=storage,
        list_groups=ListGroupsUseCase(storage),
        validate_group_limit=ValidateGroupLimitUseCase(storage),
        add_group=AddGroupUseCase(storage),
        delete_group=DeleteGroupUseCase(storage),
        list_record_groups=ListRecordGroupsUseCase(storage),
        add_record=AddRecordUseCase(storage),
        count_records=CountRecordsUseCase(storage),
        get_record=GetRecordUseCase(storage),
        edit_record=EditRecordUseCase(storage),
        delete_record=DeleteRecordUseCase(storage),
        grant_admin=GrantAdminUseCase(storage),
        list_admins=ListAdminsUseCase(storage),
        revoke_admin=RevokeAdminUseCase(storage),
        owners=settings.owners,
        group_limit=settings.group_limit,
    )


def build_dispatcher(dependencies: AppDependencies | None = None) -> Dispatcher:
    """Create and configure the application dispatcher."""

    logger.debug("Building dispatcher")
    dispatcher = Dispatcher()
    dispatcher.include_routers(system_router, group_router, record_router, admin_router)
    dispatcher.startup.register(on_startup)
    (dependencies or build_dependencies()).register(dispatcher)
    logger.debug("Dispatcher configured routers=%s", 4)
    return dispatcher


async def on_startup(**_: object) -> None:
    """Run application startup steps before polling updates."""

    logger.debug("Running startup hook storage_path=%s", JSON_PATH)
    await ensure_json_storage(JSON_PATH)
    logger.debug("Startup hook completed storage_path=%s", JSON_PATH)
