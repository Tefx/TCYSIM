class ReqOpRejectionError(Exception):
    pass


class RORUndefinedError(ReqOpRejectionError):
    pass


class RORAcquireFail(ReqOpRejectionError):
    pass


class RORBoxBeingOperatedError(ReqOpRejectionError):
    pass


class RORBoxHasUndoneRelocation(ReqOpRejectionError):
    pass


class ROREquipmentConflictError(ReqOpRejectionError):
    pass
