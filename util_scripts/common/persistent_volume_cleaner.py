"""
Module contains script that removes the EO namespace and all stuck PVs and PVCs if any exist
"""
from libs.common.pv_cleaner.persistent_volume_cleaner import PersistentVolumeCleaner
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config


if __name__ == "__main__":
    print_with_highlight(
        """
Cleans up remaining:
    - The eo-deploy namespace
    - All available PVs, PVCs on the k8s cluster
    - All VIM zone volumes attached to the eo-deploy namespace
"""
    )
    pv_cleaner = PersistentVolumeCleaner(active_site_config)
    pv_cleaner.remove_namespace_pv_pvc_and_vim_volumes()
    print_with_highlight("The script has been completed successfully")
