# Data Transfer Objects (DTO) Architecture

## Overview

This package contains all Data Transfer Objects used for API request/response type validation using Pydantic.

## Architecture Philosophy

**Long-term goal:** All API routes should use DTOs to ensure strong typing and clear contracts between frontend and backend.

**Current status:** This is a Proof of Concept (POC) with partial DTO adoption:
- Some routes already use dedicated DTOs ✅
- Other routes define their input/output directly in the route handlers ⚠️

## Future Migration

As the project matures, all routes should be refactored to:
1. Define request/response schemas in DTOs
2. Import and use them in route handlers
3. Provide clear API documentation through type hints

## Module Organization

- `chat.py` - Chat session responses
- `correctplainquestion.py` - Question correction request/response
- `deletechapter.py` - Delete chapter operations
- `deletechat.py` - Delete chat session operations
- `fetchallchats.py` - Fetch all chat sessions
- `fetchchat.py` - Fetch specific chat session
- `fetchexercise.py` - Fetch exercise responses
- `login.py` - Authentication request/response
- `markchapter.py` - Mark chapter completion
- `markcorrectedQCM.py` - Mark QCM as corrected
- `renamechapter.py` - Rename chapter operations
- `renamechat.py` - Rename chat session operations
- `signup.py` - User registration request/response

## Benefits

✅ Type safety and IDE autocompletion
✅ Automatic request validation
✅ Clear API documentation
✅ Easy to maintain and refactor
✅ Better error handling
