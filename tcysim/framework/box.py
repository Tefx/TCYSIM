from tcysim.libc import CBox, CBoxState

BoxState = CBoxState

class Box(CBox):
    STATE = BoxState
