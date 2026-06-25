from .room import router as room_router

# NOTE: the old single-player vs-AI routes (game/analysis/stats) are left on
# disk but intentionally not imported here, so the app no longer depends on the
# AI module or the database. Re-add them here to re-enable those features.
