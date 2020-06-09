class ReqOpRejectionError(Exception):
    pass


class RORUndefinedError(ReqOpRejectionError):
    pass


class RORBoxBeingOperatedError(ReqOpRejectionError):
    pass


class ROREquipmentConflictError(ReqOpRejectionError):
    pass
