
def get_all_subclasses_of_type( cls_type, cls ):
        """
            Gets all subclasses, including indirect subclasses
            :param cls_type:   the type of class
            :param cls:        Class to get subclasses from
        """
        if not issubclass( cls, cls_type ):
            print(cls, f"is not a subclass of {cls_type.__name__}")
            return []

        direct_sc = cls.__subclasses__()
        indirect_sc = []

        # get all the subclass from the subclasses found from cls.
        for sc in direct_sc:
            indirect_sc.extend( get_all_subclasses_of_type( cls_type, sc ) )

        return [ *direct_sc, *indirect_sc ]
