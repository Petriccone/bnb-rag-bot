# Fix for Vercel Deployment

The "500: INTERNAL_SERVER_ERROR" / "FUNCTION_INVOCATION_FAILED" on Vercel was likely caused by `platform_backend` being a namespace package (missing `__init__.py`) instead of a regular package.

## Diagnosis
- The Vercel entry point is `index.py` (root), which imports `platform_backend.main`.
- `platform_backend/main.py` uses relative imports (e.g., `from .routers import ...`).
- Relative imports require the parent directory to be a Python package.
- `platform_backend/__init__.py` was missing, causing import errors in strict environments like Vercel.
- **Phase 2:** conflicting `api/index.py` might have caused Vercel to create a secondary function entry point that failed due to path issues.

## The Fix
1.  Created `platform_backend/__init__.py`.
2.  Renamed `api/index.py` to `api/index.py.bak` to ensure Vercel only uses the root `index.py` as configured in `vercel.json`.

## Next Steps
1.  **Commit and Push**: You must commit the new `platform_backend/__init__.py` to your Git repository.
2.  **Redeploy**: Vercel should automatically redeploy when you push.
3.  **Verify**: Access `https://bnb-rag-api.vercel.app/docs` or `https://bnb-rag-api.vercel.app/health` to confirm it works.
