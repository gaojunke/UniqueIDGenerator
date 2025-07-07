def classFactory(iface):
    from .unique_id_generator import UniqueIDGenerator
    return UniqueIDGenerator(iface)
