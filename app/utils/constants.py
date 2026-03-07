"""Application-wide constants"""


class RoleNames:
    """Role name constants matching database entries"""
    
    SYSTEM_ADMIN = 'Systemadmin'    # ID: 1
    GUEST = 'Guest'                  # ID: 2
    FAMILY_ADMIN = 'Familyadmin'     # ID: 3
    
    @classmethod
    def get_all_roles(cls):
        """Get all available roles"""
        return [cls.SYSTEM_ADMIN, cls.GUEST, cls.FAMILY_ADMIN]
