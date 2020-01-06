class ReqOpRejectionError(Exception):
    pass


class RORUndefinedError(ReqOpRejectionError):
    pass


class RORAcquireFail(ReqOpRejectionError):
    pass


class RORBoxStateError(ReqOpRejectionError):
    pass


class ROREquipmentConflictError(ReqOpRejectionError):
    pass
