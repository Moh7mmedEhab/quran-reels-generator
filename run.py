"""Local development entry point and WSGI application export."""
from __future__ import annotations

import os

from app import create_app


app = create_app()


if __name__ == "__main__":
    # Keep the built-in server available for the documented local workflow,
    # but never enable the debugger or reloader unless explicitly requested.
    debug = bool(app.config.get("DEBUG", False))
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=debug,
        use_reloader=debug,
        threaded=True,
    )
