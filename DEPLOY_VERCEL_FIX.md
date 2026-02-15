# Fix for Vercel Deployment

The "500: INTERNAL_SERVER_ERROR" / "FUNCTION_INVOCATION_FAILED" on Vercel was caused by a combination of issues: missing package structure, entry point conflicts, and background threads incompatible with serverless environments.

## Root Causes
1.  **Missing `__init__.py`**: `platform_backend` was a namespace package, breaking relative imports.
2.  **Entry Point Conflict**: `api/index.py` existed but was not the intended entry point, confusing Vercel's builder.
3.  **Background Threads**: The application attempted to start a background worker (for message buffering) in `lifespan`. Serverless functions freeze execution between requests, causing threads to hang or crash the function.

## The Solution
1.  **Package Structure**: Created `platform_backend/__init__.py`.
2.  **Robust Entry Point**: Created a new `api/index.py` that explicitly adds the project root to `sys.path` and imports the app correctly.
3.  **Safer Lifespan**: Modified `platform_backend/main.py` to **disable the background worker** when running on Vercel (`os.environ.get("VERCEL")`).
4.  **Configuration**: Updated `vercel.json` to explicitly use `api/index.py` as the build source and destination.

## Verification
- Local import test passed confirming `api/index.py` loads the app correctly.
- Vercel should now deploy successfully. Access `https://bnb-rag-api.vercel.app/docs` to verify.
