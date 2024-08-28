"""Module that stores script for creating EVNFM user after sites are installed"""

from core_libs.eo.evnfm.users.users_test_data import UsersTestData, UserPrivileges

from apps.evnfm.evnfm_app import EvnfmApp
from libs.common.constants import GrEnvVariables
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config


def main() -> None:
    """
    Method that creates new EVNFM user
    """
    evnfm_app = EvnfmApp(active_site_config)

    logger.info(f"Create EVMFM user with name {evnfm_app.user_name!r}")

    test_data = UsersTestData.get_create_user_json(
        name=evnfm_app.user_name,
        roles=[
            UserPrivileges.EVNFM_SUPER_USER_ROLE,
            UserPrivileges.VM_VNFM_VIEW_WFS,
            UserPrivileges.VM_VNFM_WFS,
            UserPrivileges.EVNFM_UI_USER_ROLE,
        ],
        password=evnfm_app.user_password,
        tenant=evnfm_app.tenant,
    )
    evnfm_app.default_api.users.create_user(test_data)
    logger.info(f"New user successfully created with name {evnfm_app.user_name=}")


if __name__ == "__main__":
    print_with_highlight(
        "Create EVNFM user after sites installation.\n"
        f"""Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}
        """
    )
    main()
