def print_status(self, request):
    equipment = request.equipment
    print("[{:.2f}]<Request/Equipment {}.{}>".format(equipment.time, str(id(request.block))[-4:], equipment.idx),
          request, equipment.current_coord(), getattr(request, "box", None))
